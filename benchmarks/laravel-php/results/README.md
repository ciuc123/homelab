# Results 2026-11-20

PHP 8.3.37, 8.4.28, 8.5.13 (official docker images), Laravel 13.43.0, 8 interleaved rounds × 5 samples per workload and version.

## 2026-11-20-gha-epyc-7763

GitHub Actions ubuntu-24.04, AMD EPYC 7763, 4 vCPU, run [44804921270](https://github.com/ciuc123/homelab/actions/runs/44804921270).

| Workload | PHP | Median ms | IQR ms | Samples | vs 8.3 |
|---|---|---:|---:|---:|---:|
| Full request (boot + route + Eloquent + Blade) | 8.3.37 | 7.366 | 7.313–7.439 | 40 |  |
| Full request (boot + route + Eloquent + Blade) | 8.4.28 | 7.437 | 7.354–7.580 | 40 | +1.0% |
| Full request (boot + route + Eloquent + Blade) | 8.5.13 | 7.204 | 7.160–7.271 | 40 | -2.2% |
| Eloquent: 1,000 posts + authors, toArray | 8.3.37 | 228.783 | 226.179–232.025 | 40 |  |
| Eloquent: 1,000 posts + authors, toArray | 8.4.28 | 229.372 | 227.659–232.967 | 40 | +0.3% |
| Eloquent: 1,000 posts + authors, toArray | 8.5.13 | 222.734 | 221.037–227.699 | 40 | -2.6% |
| Blade: render 50 posts | 8.3.37 | 2.786 | 2.763–2.811 | 40 |  |
| Blade: render 50 posts | 8.4.28 | 2.744 | 2.724–2.776 | 40 | -1.5% |
| Blade: render 50 posts | 8.5.13 | 2.668 | 2.657–2.702 | 40 | -4.2% |
| Collections: 100k items pipeline | 8.3.37 | 132.952 | 126.998–141.557 | 40 |  |
| Collections: 100k items pipeline | 8.4.28 | 132.620 | 127.655–146.643 | 40 | -0.2% |
| Collections: 100k items pipeline | 8.5.13 | 129.299 | 123.679–137.896 | 40 | -2.7% |

## 2026-11-20-gha-epyc-9v45

GitHub Actions ubuntu-24.04, AMD EPYC 9V45, 4 vCPU, run [44803515937](https://github.com/ciuc123/homelab/actions/runs/44803515937).

| Workload | PHP | Median ms | IQR ms | Samples | vs 8.3 |
|---|---|---:|---:|---:|---:|
| Full request (boot + route + Eloquent + Blade) | 8.3.37 | 3.760 | 3.737–3.785 | 40 |  |
| Full request (boot + route + Eloquent + Blade) | 8.4.28 | 3.745 | 3.714–3.755 | 40 | -0.4% |
| Full request (boot + route + Eloquent + Blade) | 8.5.13 | 3.707 | 3.685–3.739 | 40 | -1.4% |
| Eloquent: 1,000 posts + authors, toArray | 8.3.37 | 98.197 | 97.313–99.337 | 40 |  |
| Eloquent: 1,000 posts + authors, toArray | 8.4.28 | 94.838 | 93.951–95.250 | 40 | -3.4% |
| Eloquent: 1,000 posts + authors, toArray | 8.5.13 | 94.746 | 94.264–95.396 | 40 | -3.5% |
| Blade: render 50 posts | 8.3.37 | 1.190 | 1.184–1.201 | 40 |  |
| Blade: render 50 posts | 8.4.28 | 1.145 | 1.140–1.150 | 40 | -3.8% |
| Blade: render 50 posts | 8.5.13 | 1.114 | 1.112–1.122 | 40 | -6.4% |
| Collections: 100k items pipeline | 8.3.37 | 71.293 | 70.787–72.438 | 40 |  |
| Collections: 100k items pipeline | 8.4.28 | 77.918 | 76.828–79.365 | 40 | +9.3% |
| Collections: 100k items pipeline | 8.5.13 | 75.315 | 74.566–76.259 | 40 | +5.6% |

## 2026-11-20-laptop-i7-10750H

Intel Core i7-10750H laptop, WSL2 + Docker Desktop, containers pinned to 2 cores. Noisier than the runners (shared laptop). During this run the images were rebuilt once by `setup.sh` from the same code and the same seeded data.

| Workload | PHP | Median ms | IQR ms | Samples | vs 8.3 |
|---|---|---:|---:|---:|---:|
| Full request (boot + route + Eloquent + Blade) | 8.3.37 | 7.071 | 6.828–9.132 | 40 |  |
| Full request (boot + route + Eloquent + Blade) | 8.4.28 | 7.565 | 7.061–9.988 | 40 | +7.0% |
| Full request (boot + route + Eloquent + Blade) | 8.5.13 | 7.127 | 6.948–9.002 | 40 | +0.8% |
| Eloquent: 1,000 posts + authors, toArray | 8.3.37 | 218.008 | 216.190–227.357 | 40 |  |
| Eloquent: 1,000 posts + authors, toArray | 8.4.28 | 221.428 | 218.513–228.895 | 40 | +1.6% |
| Eloquent: 1,000 posts + authors, toArray | 8.5.13 | 220.344 | 218.350–259.850 | 40 | +1.1% |
| Blade: render 50 posts | 8.3.37 | 2.658 | 2.606–2.715 | 40 |  |
| Blade: render 50 posts | 8.4.28 | 2.686 | 2.654–2.748 | 40 | +1.1% |
| Blade: render 50 posts | 8.5.13 | 2.702 | 2.663–2.787 | 40 | +1.6% |
| Collections: 100k items pipeline | 8.3.37 | 150.168 | 149.329–152.327 | 40 |  |
| Collections: 100k items pipeline | 8.4.28 | 151.995 | 150.556–154.131 | 40 | +1.2% |
| Collections: 100k items pipeline | 8.5.13 | 151.103 | 149.700–153.006 | 40 | +0.6% |
