# Laravel on PHP 8.3 vs 8.4 vs 8.5

A small, reproducible benchmark of a real Laravel 13 app (not micro-benchmarks of PHP functions) on three PHP versions. It's the data behind a post on ciuculescu.com.

## What it measures

The app is the Laravel 13 skeleton plus a `posts` table (5,000 posts by 500 users, SQLite), an Eloquent model with casts and an accessor, and a Blade list view. The dependencies are pinned by `files/composer.lock` (laravel/framework 13.43.0).

| Workload | One iteration |
|---|---|
| `request` | Full request as PHP-FPM would serve it: create the app, boot it, route `/posts`, query 50 posts with authors, render Blade, terminate |
| `eloquent` | `Post::with('user')->limit(1000)->get()->toArray()` |
| `blade` | Render the list view for 50 already-loaded posts |
| `collections` | A map → filter → groupBy → sum → sort pipeline over 100,000 items |

**Settings (the same for every version):**
- Official `php:<v>-cli` images.
- OPcache on (`opcache.enable_cli=1`), JIT off, `zend.assertions=-1`.
- `APP_ENV=production`, `APP_DEBUG=false`, `php artisan optimize` (config, routes and views cached).
- Array session and cache drivers, so no disk writes inside a request.

**Method:**
- Each process warms up first (OPcache, caches), then takes 5 samples. Each sample is the mean time of N iterations.
- `run.sh` runs `ROUNDS` rounds. In each round, every workload runs on every version, in a shuffled order, so slow periods of the machine hit all versions equally.
- Each container is pinned to the same CPU cores (`--cpuset-cpus`).
- The summary reports the median and the interquartile range of all samples.

## Run it

```bash
./setup.sh                                          # builds the app and lbench:8.3/8.4/8.5 images
ROUNDS=8 OUT=results.jsonl CPUS=2-3 ./run.sh         # about 30 minutes on a laptop
python3 summarize.py results.jsonl
```

Or on GitHub's runners: Actions → "PHP version benchmark (Laravel)" → Run workflow. The results are attached to the run as an artifact.

## Limits

- One app shape, SQLite, a single process: no network, no MySQL, no concurrency.
- Laptops throttle and shared CI runners have neighbours. Interleaving and medians reduce that noise but don't remove it, so read differences under about 5% as "no difference".
- JIT is off because that's the default and what most Laravel apps run with.
