| model                          |       size |     params | backend    | threads |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --: | --------------: | -------------------: |
| qwen35moe 35B.A3B IQ4_XS - 4.25 bpw |  16.87 GiB |    35.51 B | MTL,BLAS   |       6 |   1 |           pp512 |      1771.57 ± 16.16 |
| qwen35moe 35B.A3B IQ4_XS - 4.25 bpw |  16.87 GiB |    35.51 B | MTL,BLAS   |       6 |   1 |           tg128 |         71.59 ± 0.24 |
