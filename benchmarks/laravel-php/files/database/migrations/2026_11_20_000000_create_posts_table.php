<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void
    {
        Schema::create('posts', function (Blueprint $t) {
            $t->id();
            $t->foreignId('user_id')->constrained();
            $t->string('title');
            $t->string('slug')->unique();
            $t->text('body');
            $t->unsignedInteger('views')->default(0);
            $t->json('meta')->nullable();
            $t->timestamp('published_at')->index();
            $t->timestamps();
        });
    }
};
