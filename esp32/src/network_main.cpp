#ifdef HK17_NETWORK_APP
#include "hk17_math.hpp"
#include "hk17_network_config.hpp"
#include "hk17_wire.hpp"

#include <array>
#include <atomic>
#include <cinttypes>
#include <cstdio>
#include <cstring>
#include <exception>
#include <memory>
#include <string>
#include <vector>

#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_netif_ip_addr.h"
#include "esp_random.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "mqtt_client.h"
#include "nvs_flash.h"

namespace {

constexpr char TAG[] = "hk17-bob";
constexpr std::uint64_t POWERS = 257;
constexpr std::size_t MATRIX_DEGREE = 32;
constexpr EventBits_t WIFI_CONNECTED_BIT = BIT0;
constexpr std::size_t MESSAGE_QUEUE_LENGTH = 8;

using hk17::Matrix;
using hk17::Octonion;
using hk17::u64;

enum class NodeState {
    NOT_JOINED,
    PENDING_APPROVAL,
    KEY_EXCHANGE,
    ESTABLISHED,
    REJECTED,
};

EventGroupHandle_t g_wifi_events = nullptr;
QueueHandle_t g_message_queue = nullptr;
SemaphoreHandle_t g_session_mutex = nullptr;
SemaphoreHandle_t g_key_mutex = nullptr;
esp_mqtt_client_handle_t g_mqtt = nullptr;
httpd_handle_t g_http = nullptr;
std::string g_device_id;
std::string g_ip_address = "0.0.0.0";
std::atomic_bool g_wifi_connected{false};
std::atomic_bool g_mqtt_connected{false};
std::atomic<NodeState> g_node_state{NodeState::NOT_JOINED};
Octonion g_session_key_cache{};
std::atomic_bool g_key_available{false};

struct InboundMessage {
    std::string topic;
    std::vector<std::uint8_t> payload;
};

struct FragmentAssembly {
    std::string topic;
    std::vector<std::uint8_t> payload;
    std::size_t total_length{0};
    bool active{false};

    void clear() {
        topic.clear();
        payload.clear();
        total_length = 0;
        active = false;
    }
};

FragmentAssembly g_fragment;

const char* state_name(NodeState state) {
    switch (state) {
        case NodeState::NOT_JOINED: return "NOT_JOINED";
        case NodeState::PENDING_APPROVAL: return "PENDING_APPROVAL";
        case NodeState::KEY_EXCHANGE: return "KEY_EXCHANGE";
        case NodeState::ESTABLISHED: return "ESTABLISHED";
        case NodeState::REJECTED: return "REJECTED";
        default: return "UNKNOWN";
    }
}

u64 random_u64() {
    u64 value = 0;
    esp_fill_random(&value, sizeof(value));
    return value;
}

u64 random_below(u64 bound) {
    if (bound == 0) {
        throw std::runtime_error("random bound must be non-zero");
    }
    const u64 limit = UINT64_MAX - (UINT64_MAX % bound);
    while (true) {
        const u64 value = random_u64();
        if (value < limit) {
            return value % bound;
        }
    }
}

u64 random_range(u64 lower_inclusive, u64 upper_exclusive) {
    if (upper_exclusive <= lower_inclusive) {
        throw std::runtime_error("invalid random range");
    }
    return lower_inclusive + random_below(upper_exclusive - lower_inclusive);
}

std::vector<u64> random_polynomial(std::size_t coefficient_count, u64 modulus) {
    if (modulus <= 1) {
        throw std::runtime_error("polynomial modulus must be greater than one");
    }
    std::vector<u64> coefficients(coefficient_count, 0);
    for (u64& coefficient : coefficients) {
        coefficient = random_range(1, modulus);
    }
    return coefficients;
}

Octonion random_octonion(u64 modulus) {
    Octonion out{};
    for (u64& value : out) {
        value = random_below(modulus);
    }
    return out;
}

std::size_t degree_for_modulus(u64 p) {
    if (p == 13ULL) return 8;
    if (p == 251ULL) return 16;
    if (p == 65521ULL) return 32;
    if (p == 4294967279ULL) return 64;
    if (p == 18446744073709551557ULL) return 128;
    throw std::runtime_error("unsupported HK17.2 octonion modulus");
}

bool matrix_is_null(const Matrix& matrix) {
    for (const u64 value : matrix) {
        if (value != 0) return false;
    }
    return true;
}

bool octonion_is_null(const Octonion& octonion) {
    for (const u64 value : octonion) {
        if (value != 0) return false;
    }
    return true;
}

void print_octonion(const char* label, const Octonion& value) {
    std::printf("%s = (", label);
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (i != 0) std::printf(", ");
        std::printf("%" PRIu64, value[i]);
    }
    std::printf(")\n");
}

std::string topic_for(const char* suffix) {
    return std::string(HK17_BASE_TOPIC) + "/" + g_device_id + "/" + suffix;
}

void mqtt_publish(const std::string& topic, const std::vector<std::uint8_t>& payload) {
    const char* data = payload.empty() ? nullptr : reinterpret_cast<const char*>(payload.data());
    const int message_id = esp_mqtt_client_publish(
        g_mqtt,
        topic.c_str(),
        data,
        static_cast<int>(payload.size()),
        HK17_MQTT_QOS,
        0
    );
    if (message_id < 0) {
        throw std::runtime_error("MQTT publish failed for " + topic);
    }
}

void mqtt_publish_empty(const std::string& topic) {
    const int message_id = esp_mqtt_client_publish(
        g_mqtt,
        topic.c_str(),
        nullptr,
        0,
        HK17_MQTT_QOS,
        0
    );
    if (message_id < 0) {
        throw std::runtime_error("MQTT publish failed for " + topic);
    }
}

class BobSession {
public:
    void reset() {
        *this = BobSession{};
    }

    bool key_established() const {
        return octonion_stage_complete_;
    }

    Octonion session_key() const {
        return session_key_;
    }

    void process(const InboundMessage& message) {
        const std::string suffix = message.topic.substr(message.topic.find_last_of('/') + 1);

        if (suffix == "matrix_parameters") {
            const auto params = hk17::wire::decode_matrix_parameters(message.payload.data(), message.payload.size());
            A_ = params.A;
            B_ = params.B;
            q_ = params.q;
            u_ = params.u;
            v_ = params.v;
            have_matrix_parameters_ = true;
            g_node_state = NodeState::KEY_EXCHANGE;
            ESP_LOGI(TAG, "Matrix parameters received (q=%" PRIu64 ", u=%u, v=%u)", q_, u_, v_);
            try_matrix_stage();
            return;
        }

        if (suffix == "ta") {
            ta_payload_ = message.payload;
            have_ta_ = true;
            g_node_state = NodeState::KEY_EXCHANGE;
            ESP_LOGI(TAG, "TA received (%u bytes)", static_cast<unsigned>(ta_payload_.size()));
            try_matrix_stage();
            return;
        }

        if (suffix == "octonion_parameters") {
            const auto params = hk17::wire::decode_octonion_parameters(message.payload.data(), message.payload.size());
            p_ = params.p;
            oA_ = params.oA;
            have_octonion_parameters_ = true;
            g_node_state = NodeState::KEY_EXCHANGE;
            ESP_LOGI(TAG, "Octonion parameters received (p=%" PRIu64 ")", p_);
            try_octonion_stage();
            return;
        }

        if (suffix == "ra") {
            ra_payload_ = message.payload;
            have_ra_ = true;
            g_node_state = NodeState::KEY_EXCHANGE;
            ESP_LOGI(TAG, "rA received (%u bytes)", static_cast<unsigned>(ra_payload_.size()));
            try_octonion_stage();
            return;
        }
    }

private:
    void try_matrix_stage() {
        if (matrix_stage_complete_ || !have_matrix_parameters_ || !have_ta_) return;

        ESP_LOGI(TAG, "Starting Bob matrix stage");
        const Matrix TA = hk17::wire::decode_matrix(ta_payload_.data(), ta_payload_.size(), q_);

        const std::vector<u64> j = random_polynomial(MATRIX_DEGREE, q_);
        Matrix J = hk17::calculate_matrix_polynomial(A_, j.data(), j.size(), q_);
        if (matrix_is_null(J)) {
            throw std::runtime_error("J = j(A) is the null matrix");
        }

        Matrix J_u = hk17::matrix_power(J, u_, q_);
        Matrix J_v = hk17::matrix_power(J, v_, q_);

        Matrix temp = hk17::matrix_multiply(J_u, B_, q_);
        Matrix TB = hk17::matrix_multiply(temp, J_v, q_);

        temp = hk17::matrix_multiply(J_u, TA, q_);
        MB_ = hk17::matrix_multiply(temp, J_v, q_);
        if (matrix_is_null(MB_)) {
            throw std::runtime_error("shared matrix MB is null");
        }

        mqtt_publish(topic_for("tb"), hk17::wire::encode_matrix(TB, q_));
        matrix_stage_complete_ = true;
        ESP_LOGI(TAG, "TB sent; Bob matrix stage complete");

        Matrix{}.swap(A_);
        Matrix{}.swap(B_);
        std::vector<std::uint8_t>{}.swap(ta_payload_);

        try_octonion_stage();
    }

    void try_octonion_stage() {
        if (octonion_stage_complete_ || !matrix_stage_complete_ || !have_octonion_parameters_ || !have_ra_) return;

        ESP_LOGI(TAG, "Starting Bob octonion stage");
        const Octonion rA = hk17::wire::decode_octonion(ra_payload_.data(), ra_payload_.size(), p_);

        const hk17::ObDerivation ob = hk17::derive_ob(MB_, p_);
        if (ob.selected_configuration == 0) {
            throw std::runtime_error("none of the four oB candidates is invertible");
        }
        const Octonion oB = ob.selected;
        ESP_LOGI(TAG, "oB derived using configuration %u", static_cast<unsigned>(ob.selected_configuration));

        const std::size_t degree = degree_for_modulus(p_);
        const u64 n = random_range(2, POWERS);
        const std::vector<u64> h = random_polynomial(degree, p_);
        const Octonion oS2 = random_octonion(p_);

        const Octonion h_oA = hk17::calculate_f(oA_, h.data(), h.size(), p_);

        Octonion shifted{};
        for (std::size_t i = 0; i < hk17::OCTONION_COMPONENTS; ++i) {
            shifted[i] = hk17::mod_sub(oS2[i], oA_[i], p_);
        }

        const Octonion h_shifted = hk17::calculate_f(shifted, h.data(), h.size(), p_);
        const Octonion h1 = hk17::oct_power(h_oA, n, p_);
        const Octonion h2 = hk17::oct_power(h_shifted, n, p_);
        const Octonion h_autoconvolution = hk17::oct_multiply(h1, h2, p_);
        rB_ = hk17::oct_multiply(h_autoconvolution, oB, p_);

        const Octonion oB_inverse = hk17::octonion_reciprocal(oB, p_);
        const Octonion recovered_f = hk17::oct_multiply(rA, oB_inverse, p_);
        session_key_ = hk17::oct_multiply(recovered_f, rB_, p_);
        if (octonion_is_null(session_key_)) {
            throw std::runtime_error("generated Bob session key is null");
        }

        mqtt_publish(topic_for("rb"), hk17::wire::encode_octonion(rB_, p_));
        octonion_stage_complete_ = true;

        ESP_LOGI(TAG, "rB sent");
        ESP_LOGI(TAG, "HK17.2 KEY ESTABLISHED for %s", g_device_id.c_str());
        print_octonion("kB", session_key_);

        Matrix{}.swap(MB_);
        std::vector<std::uint8_t>{}.swap(ra_payload_);
    }

    u64 q_{0};
    std::uint16_t u_{0};
    std::uint16_t v_{0};
    Matrix A_;
    Matrix B_;
    Matrix MB_;
    std::vector<std::uint8_t> ta_payload_;
    bool have_matrix_parameters_{false};
    bool have_ta_{false};
    bool matrix_stage_complete_{false};

    u64 p_{0};
    Octonion oA_{};
    std::vector<std::uint8_t> ra_payload_;
    bool have_octonion_parameters_{false};
    bool have_ra_{false};
    bool octonion_stage_complete_{false};

    Octonion rB_{};
    Octonion session_key_{};
};

BobSession g_session;

void clear_local_key() {
    if (xSemaphoreTake(g_key_mutex, pdMS_TO_TICKS(500)) == pdTRUE) {
        g_session_key_cache = Octonion{};
        g_key_available = false;
        xSemaphoreGive(g_key_mutex);
    }
}

void cache_session_key(const Octonion& key) {
    if (xSemaphoreTake(g_key_mutex, pdMS_TO_TICKS(500)) == pdTRUE) {
        g_session_key_cache = key;
        g_key_available = true;
        xSemaphoreGive(g_key_mutex);
    }
}

bool copy_session_key(Octonion& out) {
    bool available = false;
    if (xSemaphoreTake(g_key_mutex, pdMS_TO_TICKS(500)) == pdTRUE) {
        available = g_key_available;
        if (available) out = g_session_key_cache;
        xSemaphoreGive(g_key_mutex);
    }
    return available;
}

bool request_join() {
    if (!g_mqtt_connected || g_mqtt == nullptr) {
        ESP_LOGW(TAG, "Cannot request JOIN: MQTT is not connected");
        return false;
    }
    const NodeState state = g_node_state.load();
    if (state != NodeState::NOT_JOINED && state != NodeState::REJECTED) {
        ESP_LOGW(TAG, "JOIN request ignored while node state is %s", state_name(state));
        return false;
    }

    if (xSemaphoreTake(g_session_mutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
        g_session.reset();
        xSemaphoreGive(g_session_mutex);
    } else {
        ESP_LOGE(TAG, "Could not reset Bob session for JOIN");
        return false;
    }
    clear_local_key();
    mqtt_publish_empty(std::string(HK17_BASE_TOPIC) + "/join/" + g_device_id);
    g_node_state = NodeState::PENDING_APPROVAL;
    ESP_LOGI(TAG, "JOIN request sent for %s; waiting for KMS approval", g_device_id.c_str());
    return true;
}

bool leave_network() {
    if (g_node_state == NodeState::KEY_EXCHANGE) {
        ESP_LOGW(TAG, "LEAVE is not accepted while HK17.2 exchange is running");
        return false;
    }
    if (g_mqtt_connected && g_mqtt != nullptr) {
        mqtt_publish_empty(std::string(HK17_BASE_TOPIC) + "/leave/" + g_device_id);
    }
    if (xSemaphoreTake(g_session_mutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
        g_session.reset();
        xSemaphoreGive(g_session_mutex);
    }
    clear_local_key();
    g_node_state = NodeState::NOT_JOINED;
    ESP_LOGI(TAG, "Node left HK17.2 network session");
    return true;
}

void print_status() {
    std::printf("device_id: %s\n", g_device_id.c_str());
    std::printf("IP: %s\n", g_ip_address.c_str());
    std::printf("Wi-Fi: %s\n", g_wifi_connected ? "connected" : "disconnected");
    std::printf("MQTT: %s\n", g_mqtt_connected ? "connected" : "disconnected");
    std::printf("Network state: %s\n", state_name(g_node_state));
    std::printf("Session key: %s\n", g_key_available ? "established" : "not available");
}

void queue_complete_message(const std::string& topic, std::vector<std::uint8_t>&& payload) {
    auto* message = new InboundMessage{topic, std::move(payload)};
    if (xQueueSend(g_message_queue, &message, pdMS_TO_TICKS(100)) != pdTRUE) {
        delete message;
        ESP_LOGE(TAG, "Inbound message queue full; dropping %s", topic.c_str());
    }
}

void handle_mqtt_data(esp_mqtt_event_handle_t event) {
    const std::size_t total = static_cast<std::size_t>(event->total_data_len);
    const std::size_t offset = static_cast<std::size_t>(event->current_data_offset);
    const std::size_t chunk = static_cast<std::size_t>(event->data_len);

    if (offset == 0) {
        g_fragment.clear();
        g_fragment.active = true;
        g_fragment.total_length = total;
        if (event->topic != nullptr && event->topic_len > 0) {
            g_fragment.topic.assign(event->topic, event->topic_len);
        }
        g_fragment.payload.resize(total);
    }

    if (!g_fragment.active || offset + chunk > g_fragment.payload.size()) {
        ESP_LOGE(TAG, "Invalid fragmented MQTT payload");
        g_fragment.clear();
        return;
    }

    if (chunk > 0) {
        std::memcpy(g_fragment.payload.data() + offset, event->data, chunk);
    }

    if (offset + chunk == total) {
        queue_complete_message(g_fragment.topic, std::move(g_fragment.payload));
        g_fragment.clear();
    }
}

void mqtt_event_handler(void*, esp_event_base_t, std::int32_t event_id, void* event_data) {
    auto* event = static_cast<esp_mqtt_event_handle_t>(event_data);

    switch (static_cast<esp_mqtt_event_id_t>(event_id)) {
        case MQTT_EVENT_CONNECTED: {
            g_mqtt_connected = true;
            ESP_LOGI(TAG, "Connected to Mosquitto using MQTT 3.1.1");

            const std::array<std::string, 6> subscriptions{
                topic_for("matrix_parameters"),
                topic_for("ta"),
                topic_for("octonion_parameters"),
                topic_for("ra"),
                topic_for("join_status"),
                topic_for("management"),
            };
            for (const auto& topic : subscriptions) {
                const int message_id = esp_mqtt_client_subscribe(g_mqtt, topic.c_str(), HK17_MQTT_QOS);
                if (message_id < 0) {
                    ESP_LOGE(TAG, "Failed to subscribe %s", topic.c_str());
                }
            }

            ESP_LOGI(TAG, "Node is connected but not joined. Use web UI or serial command 'join'.");
            break;
        }

        case MQTT_EVENT_DATA:
            handle_mqtt_data(event);
            break;

        case MQTT_EVENT_DISCONNECTED:
            g_mqtt_connected = false;
            ESP_LOGW(TAG, "Disconnected from MQTT broker");
            break;

        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT transport error");
            break;

        default:
            break;
    }
}

void worker_task(void*) {
    while (true) {
        InboundMessage* raw = nullptr;
        if (xQueueReceive(g_message_queue, &raw, portMAX_DELAY) != pdTRUE || raw == nullptr) {
            continue;
        }
        std::unique_ptr<InboundMessage> message(raw);
        try {
            const std::string suffix = message->topic.substr(message->topic.find_last_of('/') + 1);
            if (suffix == "management") {
                const std::string command(message->payload.begin(), message->payload.end());
                if (command == "REMOVE") {
                    if (xSemaphoreTake(g_session_mutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
                        g_session.reset();
                        xSemaphoreGive(g_session_mutex);
                    }
                    clear_local_key();
                    g_node_state = NodeState::NOT_JOINED;
                    ESP_LOGW(TAG, "KMS administratively removed this node from the network");
                } else {
                    ESP_LOGW(TAG, "Ignoring unknown KMS management command: %s", command.c_str());
                }
                continue;
            }
            if (suffix == "join_status") {
                const std::string status(message->payload.begin(), message->payload.end());
                if (status == "APPROVED") {
                    g_node_state = NodeState::KEY_EXCHANGE;
                    ESP_LOGI(TAG, "KMS approved JOIN request");
                } else if (status == "REJECTED") {
                    if (xSemaphoreTake(g_session_mutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
                        g_session.reset();
                        xSemaphoreGive(g_session_mutex);
                    }
                    clear_local_key();
                    g_node_state = NodeState::REJECTED;
                    ESP_LOGW(TAG, "KMS rejected JOIN request");
                }
                continue;
            }

            if (xSemaphoreTake(g_session_mutex, portMAX_DELAY) != pdTRUE) {
                throw std::runtime_error("could not lock Bob session");
            }
            try {
                g_session.process(*message);
                if (g_session.key_established()) {
                    cache_session_key(g_session.session_key());
                    g_node_state = NodeState::ESTABLISHED;
                }
                xSemaphoreGive(g_session_mutex);
            } catch (...) {
                xSemaphoreGive(g_session_mutex);
                throw;
            }
        } catch (const std::exception& exc) {
            ESP_LOGE(TAG, "HK17.2 Bob failure while processing %s: %s", message->topic.c_str(), exc.what());
        }
    }
}

void wifi_event_handler(void*, esp_event_base_t event_base, std::int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(g_wifi_events, WIFI_CONNECTED_BIT);
        g_wifi_connected = false;
        ESP_LOGW(TAG, "Wi-Fi disconnected; reconnecting");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        auto* event = static_cast<ip_event_got_ip_t*>(event_data);
        char ip[20]{};
        std::snprintf(ip, sizeof(ip), IPSTR, IP2STR(&event->ip_info.ip));
        g_ip_address = ip;
        g_wifi_connected = true;
        xEventGroupSetBits(g_wifi_events, WIFI_CONNECTED_BIT);
        ESP_LOGI(TAG, "Wi-Fi connected; IP=%s", g_ip_address.c_str());
    }
}

void initialize_wifi() {
    g_wifi_events = xEventGroupCreate();
    if (g_wifi_events == nullptr) {
        throw std::runtime_error("could not create Wi-Fi event group");
    }

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init_config));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, nullptr));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, nullptr));

    wifi_config_t wifi_config{};
    std::strncpy(reinterpret_cast<char*>(wifi_config.sta.ssid), HK17_WIFI_SSID, sizeof(wifi_config.sta.ssid) - 1);
    std::strncpy(reinterpret_cast<char*>(wifi_config.sta.password), HK17_WIFI_PASSWORD, sizeof(wifi_config.sta.password) - 1);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_OPEN;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Connecting to Wi-Fi SSID %s", HK17_WIFI_SSID);
    xEventGroupWaitBits(g_wifi_events, WIFI_CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
}

void initialize_device_id() {
    std::uint8_t mac[6]{};
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    char buffer[32]{};
    std::snprintf(
        buffer,
        sizeof(buffer),
        "esp32-%02x%02x%02x%02x%02x%02x",
        mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]
    );
    g_device_id = buffer;
    ESP_LOGI(TAG, "device_id=%s", g_device_id.c_str());
}

void initialize_mqtt() {
    esp_mqtt_client_config_t config{};
    config.broker.address.uri = HK17_MQTT_BROKER_URI;
    config.credentials.client_id = g_device_id.c_str();
    config.session.keepalive = HK17_MQTT_KEEPALIVE_SECONDS;
    config.session.protocol_ver = MQTT_PROTOCOL_V_3_1_1;
    config.buffer.size = 1024;
    config.buffer.out_size = 1024;

    g_mqtt = esp_mqtt_client_init(&config);
    if (g_mqtt == nullptr) {
        throw std::runtime_error("esp_mqtt_client_init failed");
    }

    ESP_ERROR_CHECK(esp_mqtt_client_register_event(g_mqtt, MQTT_EVENT_ANY, mqtt_event_handler, nullptr));
    ESP_ERROR_CHECK(esp_mqtt_client_start(g_mqtt));
}

constexpr char NODE_HTML[] = R"HTML(<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HK17.2 Node</title>
<style>:root{color-scheme:dark}body{margin:0;background:#101216;color:#eef2f7;font:15px system-ui}main{max-width:700px;margin:auto;padding:28px 18px}.card{background:#181c22;border:1px solid #2a3039;border-radius:12px;padding:18px;margin:12px 0}.row{display:flex;justify-content:space-between;gap:20px;padding:8px 0;border-bottom:1px solid #2a3039}.row:last-child{border:0}.muted{color:#9ea8b6}.mono{font-family:monospace}button{padding:9px 12px;border:1px solid #39414d;border-radius:8px;background:#232a34;color:#eef2f7;cursor:pointer;margin-right:7px}button:disabled{opacity:.45;cursor:not-allowed;border-color:#2a3039}.ok{color:#62d394}.warn{color:#f2c14e}.bad{color:#ff6b6b}</style></head>
<body><main><h1>HK17.2 Node</h1><div class="muted">ESP32 / Bob · Local laboratory interface</div><div class="card"><div class="row"><span>Device ID</span><b id="id" class="mono">—</b></div><div class="row"><span>IP</span><b id="ip" class="mono">—</b></div><div class="row"><span>Wi-Fi</span><b id="wifi">—</b></div><div class="row"><span>MQTT</span><b id="mqtt">—</b></div><div class="row"><span>Network state</span><b id="state">—</b></div><div class="row"><span>Session key</span><span><b id="key" class="mono">••••••••••••••••</b> <button id="eye" onclick="toggleKey()">👁 Show</button></span></div></div><button id="join-btn" onclick="action('/api/join')" disabled>Request network join</button><button id="leave-btn" onclick="action('/api/leave')" disabled>Leave network</button></main>
<script>let visible=false;async function action(u){const r=await fetch(u,{method:'POST'});if(!r.ok)alert(await r.text());await refresh()}async function toggleKey(){if(visible){visible=false;document.getElementById('key').textContent='••••••••••••••••';document.getElementById('eye').textContent='👁 Show';return}const r=await fetch('/api/key',{cache:'no-store'});if(!r.ok){alert('Session key is not established');return}const x=await r.json();document.getElementById('key').textContent='('+x.key.join(', ')+')';document.getElementById('eye').textContent='Hide';visible=true}function paint(id,ok){const el=document.getElementById(id);el.className=ok?'ok':'bad'}async function refresh(){const r=await fetch('/api/status',{cache:'no-store'});const s=await r.json();document.getElementById('id').textContent=s.device_id;document.getElementById('ip').textContent=s.ip;document.getElementById('wifi').textContent=s.wifi?'connected':'disconnected';document.getElementById('mqtt').textContent=s.mqtt?'connected':'disconnected';paint('wifi',s.wifi);paint('mqtt',s.mqtt);document.getElementById('state').textContent=s.state;const stateEl=document.getElementById('state');stateEl.className=s.state==='ESTABLISHED'?'ok':(s.state==='REJECTED'?'bad':(s.state==='PENDING_APPROVAL'||s.state==='KEY_EXCHANGE'?'warn':''));const joinBtn=document.getElementById('join-btn'),leaveBtn=document.getElementById('leave-btn');const joinState=s.state==='NOT_JOINED'||s.state==='REJECTED';joinBtn.disabled=!(s.mqtt&&joinState);joinBtn.title=!s.mqtt?'MQTT broker is disconnected':(!joinState?'JOIN is only available from NOT_JOINED or REJECTED':'');leaveBtn.disabled=s.state==='NOT_JOINED'||s.state==='KEY_EXCHANGE';leaveBtn.title=s.state==='KEY_EXCHANGE'?'LEAVE is disabled while HK17.2 is running':(s.state==='NOT_JOINED'?'Node is not joined':'');const keyEl=document.getElementById('key'),eyeEl=document.getElementById('eye');if(!s.key_available){visible=false;keyEl.textContent='not established';eyeEl.style.display='none'}else{eyeEl.style.display='inline-block';if(!visible)keyEl.textContent='••••••••••••••••'}}refresh();setInterval(refresh,1000)</script></body></html>)HTML";

esp_err_t send_json(httpd_req_t* req, const std::string& body) {
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_send(req, body.c_str(), body.size());
}

esp_err_t root_handler(httpd_req_t* req) {
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    return httpd_resp_send(req, NODE_HTML, HTTPD_RESP_USE_STRLEN);
}

esp_err_t status_handler(httpd_req_t* req) {
    char body[384]{};
    std::snprintf(
        body,
        sizeof(body),
        "{\"device_id\":\"%s\",\"ip\":\"%s\",\"wifi\":%s,\"mqtt\":%s,\"state\":\"%s\",\"key_available\":%s}",
        g_device_id.c_str(),
        g_ip_address.c_str(),
        g_wifi_connected ? "true" : "false",
        g_mqtt_connected ? "true" : "false",
        state_name(g_node_state),
        g_key_available ? "true" : "false"
    );
    return send_json(req, body);
}

esp_err_t join_handler(httpd_req_t* req) {
    if (!request_join()) {
        httpd_resp_set_status(req, "409 Conflict");
        httpd_resp_set_type(req, "text/plain");
        httpd_resp_sendstr(req, "JOIN request is not available in the current state");
        return ESP_OK;
    }
    return send_json(req, "{\"status\":\"requested\"}");
}

esp_err_t leave_handler(httpd_req_t* req) {
    if (!leave_network()) {
        httpd_resp_set_status(req, "409 Conflict");
        httpd_resp_set_type(req, "text/plain");
        httpd_resp_sendstr(req, "LEAVE request is not available in the current state");
        return ESP_OK;
    }
    return send_json(req, "{\"status\":\"left\"}");
}

esp_err_t key_handler(httpd_req_t* req) {
    Octonion key{};
    if (!copy_session_key(key)) {
        httpd_resp_set_status(req, "409 Conflict");
        httpd_resp_set_type(req, "text/plain");
        httpd_resp_sendstr(req, "Session key is not established");
        return ESP_OK;
    }
    char body[320]{};
    std::snprintf(
        body,
        sizeof(body),
        "{\"key\":[%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 "]}",
        key[0], key[1], key[2], key[3], key[4], key[5], key[6], key[7]
    );
    return send_json(req, body);
}

void initialize_http_server() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_uri_handlers = 8;
    config.stack_size = 6144;
    if (httpd_start(&g_http, &config) != ESP_OK) {
        throw std::runtime_error("could not start ESP32 HTTP server");
    }

    const httpd_uri_t routes[] = {
        {"/", HTTP_GET, root_handler, nullptr},
        {"/api/status", HTTP_GET, status_handler, nullptr},
        {"/api/join", HTTP_POST, join_handler, nullptr},
        {"/api/leave", HTTP_POST, leave_handler, nullptr},
        {"/api/key", HTTP_GET, key_handler, nullptr},
    };
    for (const auto& route : routes) {
        ESP_ERROR_CHECK(httpd_register_uri_handler(g_http, &route));
    }
    ESP_LOGI(TAG, "Node web UI: http://%s/", g_ip_address.c_str());
}

void cli_task(void*) {
    std::printf("Serial commands: help | status | join | leave | show-key\n");
    char line[80]{};
    while (true) {
        if (std::fgets(line, sizeof(line), stdin) == nullptr) {
            clearerr(stdin);
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        line[strcspn(line, "\r\n")] = '\0';
        const std::string command(line);
        if (command.empty()) continue;
        if (command == "help") {
            std::printf("help      - show commands\nstatus    - show node state\njoin      - request KMS network admission\nleave     - discard local session and leave network\nshow-key  - print locally derived kB when established\n");
        } else if (command == "status") {
            print_status();
        } else if (command == "join") {
            request_join();
        } else if (command == "leave") {
            leave_network();
        } else if (command == "show-key") {
            Octonion key{};
            if (copy_session_key(key)) print_octonion("kB", key);
            else std::printf("Session key is not established.\n");
        } else {
            std::printf("Unknown command: %s\n", command.c_str());
        }
    }
}

}  // namespace

extern "C" void app_main() {
    std::printf("====================================================================================================\n");
    std::printf("HK17.2 ESP32 / BOB DISTRIBUTED KMS CLIENT\n");
    std::printf("====================================================================================================\n");

    try {
        esp_err_t nvs_result = nvs_flash_init();
        if (nvs_result == ESP_ERR_NVS_NO_FREE_PAGES || nvs_result == ESP_ERR_NVS_NEW_VERSION_FOUND) {
            ESP_ERROR_CHECK(nvs_flash_erase());
            ESP_ERROR_CHECK(nvs_flash_init());
        } else {
            ESP_ERROR_CHECK(nvs_result);
        }

        g_message_queue = xQueueCreate(MESSAGE_QUEUE_LENGTH, sizeof(InboundMessage*));
        g_session_mutex = xSemaphoreCreateMutex();
        g_key_mutex = xSemaphoreCreateMutex();
        if (g_message_queue == nullptr || g_session_mutex == nullptr || g_key_mutex == nullptr) {
            throw std::runtime_error("could not create FreeRTOS synchronization objects");
        }
        if (xTaskCreate(worker_task, "hk17_worker", 8192, nullptr, 5, nullptr) != pdPASS) {
            throw std::runtime_error("could not create HK17 worker task");
        }
        if (xTaskCreate(cli_task, "hk17_cli", 4096, nullptr, 3, nullptr) != pdPASS) {
            throw std::runtime_error("could not create serial CLI task");
        }

        initialize_device_id();
        initialize_wifi();
        initialize_http_server();
        ESP_LOGI(TAG, "MQTT broker: %s", HK17_MQTT_BROKER_URI);
        initialize_mqtt();

        while (true) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    } catch (const std::exception& exc) {
        ESP_LOGE(TAG, "Fatal initialization error: %s", exc.what());
    }
}

#endif  // HK17_NETWORK_APP
