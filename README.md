# factset

Process Geneva data for FactSet upload.


## Todo

1. Need to get SEDOL code for equity;

2. Need to get FX rate: can we get it from factset? can we use Bloomberg FX rate?

3. Cash dividend receivable: keep it as is, but consolidate others.

4. show dividend receivable per share only on Ex date.

5. what about tax, should we use before tax or after tax number?

6. ask fund accounting, whether they have changed or created any dividend entry?

7. if HSBC is going to pay dvd in USD, but we want HKD, so what is going to happen?


## Known Issues

1. For multipart tax lot report, the fields "ExtendedDescription" and "Description3" are missing.