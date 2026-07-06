# Property Search Platform 

FastAPI and Airflow project for running custom buy-to-let property searches, scraping sale/rent listings, and calculating rental yield results.

<img width="628" height="448" alt="Screenshot 2025-07-18 at 00 23 07" src="https://github.com/user-attachments/assets/af97baef-492b-46cb-95db-31cc2279647a" />


---

### Background

This project is evolving from a proof of concept (PoC) into an API-driven product for UK buy-to-let searches. The current pipeline:
- accepts search criteria through the FastAPI API
- triggers an Airflow DAG for the scraping/calculation work
- scrapes renting and sale listings
- calculates gross and net rental yields
- stores search runs and calculated results in PostgreSQL
- returns paginated results through the API

---

### Scope

The current product flow focuses on user-submitted searches. A search run stores criteria such as postcode, location identifier, radius, property type, price range, bedroom range, and maximum pages.

---

### Technology

- **Language:** Python  
- **Containerization:** Docker, Docker Compose  
- **Workflow Orchestration:** Apache Airflow  
- **Database:** PostgreSQL
- **API:** FastAPI
- **Auth:** JWT bearer tokens
- **Migrations:** Alembic

---

### Tests

Run unit or integration tests with pytest markers:

```bash
.venv311/bin/python -m pytest -m unit
.venv311/bin/python -m pytest -m integration
```

- `unit` tests live in `api/tests/unit`
- `integration` tests live in `api/tests/integration`

Run code checks with:

```bash
.venv311/bin/ruff check .
.venv311/bin/ruff format --check .
```

---

### Data Sources

- **Sale Listings:** scraped by postcode and location identifier
- **Rental Listings:** scraped by postcode and room count
- **Stamp Duty:** Based on embedded UK tiered rules

### Outputs and Visuals

To see what a successful pipeline run looks like, here's a screenshot of the Airflow DAG after successful execution:

<img width="1124" height="514" alt="Screenshot 2025-07-22 at 08 42 03" src="https://github.com/user-attachments/assets/886ea4bb-8242-4464-8e51-bd7dbb6d7bbc" />


Results are stored in PostgreSQL and returned by the API.

---
### Data Storage

All data is stored in PostgreSQL:

| Table                         | Description                           |
|------------------------------|---------------------------------------|
| `users`                         | API users and roles                    |
| `search_runs`                   | User search criteria and run status    |
| `search_run_sale_listings`      | Raw sale listings for a search run     |
| `search_run_rent_listings`      | Raw rental listings for a search run   |
| `clean_search_run_sale_listings`| Cleaned sale listings for a search run |
| `clean_search_run_rent_listings`| Cleaned rental listings for a search run |
| `search_run_yields`             | Calculated gross/net yield results     |

---
If you have any questions or feedback, feel free to reach out to me:

Mariya Danilova
[LinkedIn](https://www.linkedin.com/in/mariya-danilova-a31788138)
