BEGIN;

CREATE TEMPORARY TABLE aged_debtor_import (
    demarcation_code TEXT,
    period_code TEXT,
    customer_group_code TEXT,
    item_code TEXT,
    bad_amount FLOAT,
    badi_amount FLOAT,
    g1_amount FLOAT,
    l1_amount FLOAT,
    l120_amount FLOAT,
    l150_amount FLOAT,
    l180_amount FLOAT,
    l30_amount FLOAT,
    l60_amount FLOAT,
    l90_amount FLOAT,
    total_amount FLOAT,
    financial_year INTEGER,
    amount_type_code TEXT,
    period_length TEXT,
    financial_period INTEGER
) ON COMMIT DROP;

\copy aged_debtor_import (demarcation_code, period_code, customer_group_code, item_code, bad_amount, badi_amount, g1_amount, l1_amount, l120_amount, l150_amount, l180_amount, l30_amount, l60_amount, l90_amount, total_amount) FROM '/home/jdb/proj/code4sa/municipal_finance/datasets/2016q3/debt_2016q3_acrmun.csv' DELIMITER ',' CSV HEADER;

delete from aged_debtor_import where item_code in (' Inc',' Ren');

UPDATE aged_debtor_import SET financial_year = cast(left(period_code, 4) AS int);
UPDATE aged_debtor_import SET amount_type_code = substr(period_code, 5) WHERE substr(period_code, 5) in ('IBY1', 'IBY2', 'ADJB', 'ORGB', 'AUDA', 'PAUD');
UPDATE aged_debtor_import SET amount_type_code = 'ACT' WHERE substr(period_code, 5) NOT in ('IBY1', 'IBY2', 'ADJB', 'ORGB', 'AUDA', 'PAUD');
UPDATE aged_debtor_import SET period_length = 'year' WHERE substr(period_code, 5, 3) NOT SIMILAR to 'M\d{2}';
UPDATE aged_debtor_import SET period_length = 'month' WHERE substr(period_code, 5, 3) SIMILAR to 'M\d{2}';
UPDATE aged_debtor_import SET financial_period = cast(right(period_code, 2) AS int) WHERE period_length = 'month';
UPDATE aged_debtor_import SET financial_period = cast(left(period_code, 4) AS int) WHERE period_length = 'year';

UPDATE aged_debtor_facts f
SET demarcation_code = i.demarcation_code,
    period_code = i.period_code,
    item_code = i.item_code,
    bad_amount = round(i.bad_amount),
    badi_amount = round(i.badi_amount),
    g1_amount = round(i.g1_amount),
    l1_amount = round(i.l1_amount),
    l120_amount = round(i.l120_amount),
    l150_amount = round(i.l150_amount),
    l180_amount = round(i.l180_amount),
    l30_amount = round(i.l30_amount),
    l60_amount = round(i.l60_amount),
    l90_amount = round(i.l90_amount),
    total_amount = round(i.total_amount),
    financial_year = i.financial_year,
    amount_type_code = i.amount_type_code,
    period_length = i.period_length,
    financial_period = i.financial_period
FROM aged_debtor_import i
WHERE f.demarcation_code = i.demarcation_code
AND f.period_code = i.period_code
AND f.customer_group_code = i.customer_group_code
AND f.item_code = i.item_code
AND (f.bad_amount != round(i.bad_amount)
  OR f.badi_amount != round(i.badi_amount)
  OR f.g1_amount != round(i.g1_amount)
  OR f.l1_amount != round(i.l1_amount)
  OR f.l120_amount != round(i.l120_amount)
  OR f.l150_amount != round(i.l150_amount)
  OR f.l180_amount != round(i.l180_amount)
  OR f.l30_amount != round(i.l30_amount)
  OR f.l60_amount != round(i.l60_amount)
  OR f.l90_amount != round(i.l90_amount)
  OR f.total_amount != round(i.total_amount));

INSERT INTO aged_debtor_facts
(
    demarcation_code,
    period_code,
    customer_group_code,
    item_code,
    bad_amount,
    badi_amount,
    l120_amount,
    l150_amount,
    l180_amount,
    l30_amount,
    l60_amount,
    l90_amount,
    total_amount,
    financial_year,
    amount_type_code,
    period_length,
    financial_period
)
SELECT demarcation_code,
       period_code,
       customer_group_code,
       item_code,
       round(bad_amount),
       round(badi_amount),
       round(l120_amount),
       round(l150_amount),
       round(l180_amount),
       round(l30_amount),
       round(l60_amount),
       round(l90_amount),
       round(total_amount),
       financial_year,
       amount_type_code,
       period_length,
       financial_period
FROM aged_debtor_import i
WHERE
    NOT EXISTS (
        SELECT 1 FROM aged_debtor_facts f
        WHERE f.demarcation_code = i.demarcation_code
        AND f.customer_group_code = i.customer_group_code
        AND f.period_code = i.period_code
        AND f.item_code = i.item_code
    );

COMMIT;
