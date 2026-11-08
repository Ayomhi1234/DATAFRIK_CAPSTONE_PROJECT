# Design Decisions Document
## Portfolio Analytics Data Engineering Capstone

### 1. Project Context

The objective of this project was to develop an automated data engineering pipeline that integrates financial datasets from multiple sources, transforms them into meaningful portfolio metrics and presents the results through an analytical dashboard.

The design prioritizes modularity, automation, data consistency, maintainability and the ability to extend the pipeline in the future.

### 2. Technology Selection and Justification

| Technology | Design Decision |
|---|---|
| Python | Selected for flexible data extraction, processing and database integration. |
| yfinance | Used to retrieve historical stock market data without manually downloading price records. |
| Google Sheets | Selected as a simple and accessible source for trade transaction records. |
| Airbyte Cloud | Used to synchronize external datasets into the central database. |
| Custom Airbyte Source | Developed to integrate historical USD/NGN exchange rates from the Frankfurter API. |
| Neon PostgreSQL | Selected as the centralized cloud database for storing ingested and transformed datasets. |
| SQLAlchemy | Used to establish Python connectivity with PostgreSQL. |
| dbt Core | Selected to build modular SQL transformations and execute data quality tests. |
| GitHub Actions | Used to automate and schedule pipeline execution. |
| Docker and Metabase | Used to deploy a local business intelligence environment for portfolio reporting. |

### 3. Data Architecture Decisions

**Multiple Data Sources**

The project integrates stock prices, trade transactions and foreign exchange rates. Each source is ingested through an appropriate mechanism rather than forcing all sources into one extraction process.

**Centralized Database**

Neon PostgreSQL was selected to provide a centralized storage environment, making the datasets accessible to dbt and Metabase.

**Staging and Analytical Modeling**

dbt staging models prepare the individual datasets before the analytical mart combines them. This separation improves organization, readability and maintainability.

**Portfolio Valuation**

The analytical mart calculates stock-level market value, cost basis and unrealized gains or losses. It also produces portfolio-level valuation in USD and NGN.

Portfolio totals are repeated across stock-level records for each date. Therefore, queries must avoid summing repeated portfolio totals.

### 4. Automation Decisions

GitHub Actions was selected to coordinate the pipeline without requiring manual execution of every stage.

The workflow supports scheduled weekday execution and manual triggering.

Airbyte handles the configured source synchronization, while dbt executes the transformation and testing operations.

### 5. Visualization Decisions

Metabase was selected because it supports direct PostgreSQL connectivity and provides a practical environment for building analytical dashboards.

The dashboard focuses on four important views:

- Portfolio valuation trends.
- Unrealized gains and losses by stock.
- Portfolio allocation by stock.
- Portfolio valuation comparison in USD and NGN.

Docker was used to run Metabase locally while keeping its application data persistent through a Docker volume.

### 6. Security and Data Management

Database credentials and sensitive configuration values are maintained outside the public source code through environment variables and GitHub secrets.

The repository excludes sensitive environment files.

The trade transaction dataset consists of synthetic records generated for educational and demonstration purposes.

### 7. Limitations and Future Considerations

The current implementation focuses on historical portfolio analysis rather than real-time trading.

Potential improvements include:

- More comprehensive data quality monitoring.
- Automated failure notifications.
- Additional portfolio performance indicators.
- More advanced forecasting and predictive analytics.
- Expanded dashboard filtering and interactivity.

### 8. Conclusion

The selected architecture provides a modular and automated approach to integrating, transforming and analyzing financial datasets.

The design demonstrates how open-source and cloud-based technologies can work together to deliver an end-to-end data engineering solution.