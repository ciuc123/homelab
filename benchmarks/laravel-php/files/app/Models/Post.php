<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
class Post extends Model
{
    protected $guarded = [];
    protected function casts(): array
    {
        return ['meta' => 'array', 'published_at' => 'datetime', 'views' => 'integer'];
    }
    public function user(): BelongsTo { return $this->belongsTo(User::class); }
    public function getExcerptAttribute(): string { return \Illuminate\Support\Str::limit(strip_tags($this->body), 140); }
}
