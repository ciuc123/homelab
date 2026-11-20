<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Posts</title></head>
<body>
<h1>Latest posts</h1>
@foreach ($posts as $post)
  <article class="post">
    <h2><a href="{{ url('/posts/'.$post->slug) }}">{{ $post->title }}</a></h2>
    <p class="meta">By {{ $post->user->name }} · {{ $post->published_at->format('M j, Y') }} · {{ number_format($post->views) }} views
      @if (!empty($post->meta['tags'])) · @foreach ($post->meta['tags'] as $tag)<span class="tag">{{ $tag }}</span>@endforeach @endif</p>
    <p>{{ $post->excerpt }}</p>
  </article>
@endforeach
</body></html>
