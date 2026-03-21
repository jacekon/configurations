#!/usr/bin/env bash

curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          { "key": "service.name", "value": { "stringValue": "curl-test-service" } }
        ]
      },
      "scopeSpans": [
        {
          "spans": [
            {
              "traceId": "0123456789abcdef0123456789abcdef",
              "spanId": "0123456789abcdef",
              "name": "test-span-from-curl",
              "startTimeUnixNano": "'$(date +%s000000000)'",
              "endTimeUnixNano": "'$(date +%s000000000)'"
            }
          ]
        }
      ]
    }
  ]
}'

