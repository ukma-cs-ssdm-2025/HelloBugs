## Pipeline Runs

| Run # | Commit SHA | Status | Start → End (min) | Deployed? | Notes |
|:----:|-------------|:-------:|:------------------:|:----------:|:------|
| 1 | 226c7c9 |  ✅ | 3,54 | ✅ | add one more test (data integrity) 
| 2 | 7c5083e| ✅ |4.8  | ✅ | change SQLite to PostgreSQL in coverage |
| 3 | cdf8ca0 | ✅ | 4,1  | ✅  | fix problems with booking creating 2.0 | 
| 4 | 0fa635e | ✅ | 4,03 | ✅ |  upd the report table + additional fixes |
| 5 | dfe6b15 | ❌ | 2,12 | ❌ | REFACTOR: harden JSON parsing in auth routes to prevent 500 on malformed input |
| 6 | 2aa9b4b| ✅|4,16 | ✅ |fix room component tests  |
| 7 | 8b5f0fa  | ✅| 4,5 |✅  |fix problem w race condition (ind task)  |
| 8 |a1a86ee | ❌ | 2,44 | ❌ | [REFACTOR] hide internal error details in 500 responses in routes |
| 9 | a08502c | ✅  | 5,47 | ✅ | [REFACTOR] 'end' is modified in isRangeFree loop in bookings_create.js. |
| 10 | 56dbc3b | ❌ | 3,2 | ❌ | fix atrerror with authorization |

---
## Aggregated Summary

### For full `develop` branch history:
- Successful: **193**
- Failed: **99**
- Cancelled: **21**
- Total completed: **313**

### Based on last 10 runs:
- Total runs: **10**
- Successful: **7**
- Failed: **3**
- Deployment success rate: **7/10**
- Deployment failure rate: **3/10**

### Pipeline duration (last 10 runs):
- Average: **3.836 min**
- Fastest: **2.12 min** (Run #5)
- Slowest: **5.47 min** (Run #9)
