# Public Launch QA

Use this checklist before publishing the Project 3 GitHub repo or linking it on the portfolio site.

## Repo Safety

Status: prepared for public GitHub.

Confirmed exclusions:

- Raw Olist CSV files are ignored.
- Large cleaned Python CSVs are ignored.
- Large curated fact/dimension CSVs are ignored.
- Local SQLite database is ignored.
- Python cache files are ignored.

Included proof files:

- Python scripts
- SQL scripts
- README
- supporting documentation
- SVG visuals
- small validation summary files
- small monthly KPI summary files
- data quality issue sample/output

## Validation QA

Open:

`data/validation_outputs/reconciliation_summary.csv`

Expected result:

| Check group | Pass | Review |
| --- | ---: | ---: |
| Python vs SQL metric checks | 14 | 0 |
| Monthly revenue checks | 25 | 0 |

Open:

`data/validation_outputs/python_sql_comparison_summary.csv`

Expected:

- Every row has `status = Pass`.
- Total revenue matches between Python and SQL.
- Item price revenue matches.
- Freight revenue matches.
- Payment revenue matches.
- Payment/order variance matches.
- Average order value matches.

## README QA

Open `README.md` and check:

- The business problem is understandable to a non-technical reviewer.
- The workflow clearly explains raw data to Python/SQL outputs to validation.
- The completed result table is visible.
- The SVG images render.
- The project does not overclaim commercial/proprietary use of the Olist data.
- The Kaggle source and license are included.

## Interview Defense QA

Be ready to explain:

- Why `total_revenue = price + freight_value`.
- Why payment revenue is tracked separately from item-plus-freight revenue.
- What payment/order variance means.
- What the Python-vs-SQL comparison proves.
- Why monthly revenue validation matters.
- What the data quality issue log is for.
- How this project feeds the Tableau dashboard in Project 4.

## Publish Sequence

1. Create an empty public GitHub repo named:
   `ecommerce-reporting-pipeline-quality-control`
2. Do not add a README, `.gitignore`, or license in GitHub because the local repo already has files.
3. From PowerShell:

```powershell
cd "D:\Documents\Portfolio\ecommerce-reporting-pipeline-quality-control"
git remote add origin https://github.com/DurellMarshall/ecommerce-reporting-pipeline-quality-control.git
git push -u origin main
```

4. Confirm the GitHub README renders correctly.
5. Confirm raw CSVs and the SQLite file are not visible in GitHub.
6. Add the repo link to Notion.
