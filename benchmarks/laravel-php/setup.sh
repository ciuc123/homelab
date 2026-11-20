#!/bin/bash
# Builds the benchmark app (Laravel skeleton + this folder's files, dependencies pinned by composer.lock)
# and one Docker image per PHP version: lbench:8.3, lbench:8.4, lbench:8.5.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf build && mkdir -p build
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/build:/w" -w /w -e COMPOSER_HOME=/tmp/c composer:2 \
  create-project --no-interaction --no-install --no-scripts laravel/laravel app "^13.0" >/dev/null
cp -r files/. build/app/
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/build/app:/app" -w /app -e COMPOSER_HOME=/tmp/c composer:2 \
  sh -c 'composer install --no-interaction --no-dev -q && cp .env.example .env && php artisan key:generate -q'
sed -i 's/^APP_ENV=.*/APP_ENV=production/; s/^APP_DEBUG=.*/APP_DEBUG=false/; s/^SESSION_DRIVER=.*/SESSION_DRIVER=array/; s/^CACHE_STORE=.*/CACHE_STORE=array/; s/^DB_CONNECTION=.*/DB_CONNECTION=sqlite/' build/app/.env
grep -q 'function posts' build/app/app/Models/User.php || \
  sed -i 's/^}$/    public function posts(): \\Illuminate\\Database\\Eloquent\\Relations\\HasMany { return $this->hasMany(Post::class); }\n}/' build/app/app/Models/User.php
grep -q "'/posts'" build/app/routes/web.php || cat >> build/app/routes/web.php <<'R'

Route::get('/posts', function () {
    $posts = \App\Models\Post::with('user')->orderByDesc('published_at')->limit(50)->get();
    return view('posts', ['posts' => $posts]);
});
R
touch build/app/database/database.sqlite
R="docker run --rm -u $(id -u):$(id -g) -v $PWD/build/app:/app -w /app php:8.3-cli"
$R php artisan migrate --force -q && $R php bench.php seed 1 && $R php artisan optimize -q
cp Dockerfile build/ && printf "app/storage/logs/*\n" > build/.dockerignore
for v in 8.3 8.4 8.5; do docker build -q --build-arg PHP=$v -t lbench:$v build >/dev/null && echo "built lbench:$v"; done
