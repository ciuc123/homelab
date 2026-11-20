<?php
// Benchmark harness: php bench.php <workload> <samples> [iterations]
// Prints one JSON line: {"php": ..., "workload": ..., "ms": [per-iteration ms for each sample]}
use Illuminate\Http\Request;

require __DIR__.'/vendor/autoload.php';

function boot() {
    $app = require __DIR__.'/bootstrap/app.php';
    $app->make(Illuminate\Contracts\Http\Kernel::class)->bootstrap();
    $app->instance('request', Request::create('/posts'));
    return $app;
}

$workload = $argv[1]; $samples = (int) $argv[2];
$iters = (int) ($argv[3] ?? ['request' => 50, 'eloquent' => 20, 'blade' => 200, 'collections' => 10, 'seed' => 1][$workload]);

if ($workload === 'seed') {
    boot();
    $db = Illuminate\Support\Facades\DB::connection();
    $db->table('posts')->delete(); $db->table('users')->delete();
    mt_srand(42);
    $words = explode(' ', 'laravel php queue eloquent docker redis cache index query test deploy release model route view job event mail policy schema migration');
    $users = [];
    for ($i = 1; $i <= 500; $i++) $users[] = ['id' => $i, 'name' => "User $i", 'email' => "user$i@example.com", 'password' => 'x', 'created_at' => now(), 'updated_at' => now()];
    foreach (array_chunk($users, 100) as $c) $db->table('users')->insert($c);
    $rows = [];
    for ($i = 1; $i <= 5000; $i++) {
        $t = implode(' ', array_map(fn() => $words[mt_rand(0, count($words) - 1)], range(1, 6)));
        $rows[] = ['user_id' => mt_rand(1, 500), 'title' => ucfirst($t), 'slug' => "post-$i", 'body' => str_repeat("<p>$t. </p>", 40),
                   'views' => mt_rand(0, 100000), 'meta' => json_encode(['tags' => array_slice($words, mt_rand(0, 15), 3)]),
                   'published_at' => now()->subMinutes($i), 'created_at' => now(), 'updated_at' => now()];
        if (count($rows) === 250) { $db->table('posts')->insert($rows); $rows = []; }
    }
    echo "seeded\n"; exit;
}

$run = match ($workload) {
    // Full framework boot + routing + Eloquent (50 posts with authors) + Blade, per request: closest to PHP-FPM with OPcache.
    'request' => function () {
        $app = require __DIR__.'/bootstrap/app.php';
        $kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
        $req = Request::create('/posts');
        $res = $kernel->handle($req);
        if ($res->getStatusCode() !== 200) { fwrite(STDERR, substr($res->getContent(), 0, 500)); exit(1); }
        $kernel->terminate($req, $res);
    },
    // Hydrate 1,000 models with their authors and serialize them.
    'eloquent' => (function () { boot(); return fn() => App\Models\Post::with('user')->limit(1000)->get()->toArray(); })(),
    // Render the list view for 50 already-loaded posts.
    'blade' => (function () { boot(); $p = App\Models\Post::with('user')->limit(50)->get();
                 return fn() => view('posts', ['posts' => $p])->render(); })(),
    // Collection pipeline over 100,000 items.
    'collections' => fn() => collect(range(1, 100000))->map(fn($i) => ['id' => $i, 'g' => $i % 100, 'v' => $i * 1.5])
                         ->filter(fn($r) => $r['id'] % 3 !== 0)->groupBy('g')->map(fn($g) => $g->sum('v'))->sortDesc()->take(10)->all(),
};

for ($i = 0; $i < max(3, intdiv($iters, 5)); $i++) $run();   // warm-up (OPcache, caches)
$out = [];
for ($s = 0; $s < $samples; $s++) {
    $t = hrtime(true);
    for ($i = 0; $i < $iters; $i++) $run();
    $out[] = round((hrtime(true) - $t) / 1e6 / $iters, 4);
}
echo json_encode(['php' => PHP_VERSION, 'workload' => $workload, 'iters' => $iters, 'ms' => $out]), "\n";
