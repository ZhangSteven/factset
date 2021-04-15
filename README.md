# factset

Process Geneva data for FactSet upload.


## Todo

1. Need to get SEDOL code for equity;

2. Get FX rate from tax lot file; getFX(date)

3. Consolidate all cash entries in taxlot;

4. show dividend receivable per share only on Ex date, with pre-tax number;

5. ask fund accounting, whether they have changed or created any dividend entry?

6. if HSBC is going to pay dvd in USD, but we want HKD, so what is going to happen?


## Known Issues

1. For multipart tax lot report, the fields "ExtendedDescription" and "Description3" are missing, but "ExtendedDescription" is useful in FX Forward;

2. FX Forward, how to join them in tax lot and cash ledger, it seems cash ledger TransID != tax lot id, and the interest rate does not match either.