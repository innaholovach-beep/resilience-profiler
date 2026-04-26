# ЛАБА 10-11 — Load & Stress Testing (JMeter)
#
# Сценарій: 100 користувачів одночасно проходять анкету
#
# Кроки для відтворення:
#   1. Відкрий JMeter
#   2. Додай Thread Group: 100 threads, ramp-up 30s, 3 iterations
#   3. Додай HTTP Request Sampler:
#      - POST /api/auth/login
#      - POST /api/survey/submit
#      - GET  /api/profile/{id}
#   4. Додай:
#      - View Results Tree
#      - Summary Report
#      - Response Time Graph
#
# Очікувані показники (Load test):
#   - Response time P95 < 500ms
#   - Error rate < 1%
#   - Throughput > 50 req/s
#
# Стрес-тест: поступово збільшуй до 500, 1000 users
# до знаходження точки відмови (>5% errors або P95 > 2000ms)
