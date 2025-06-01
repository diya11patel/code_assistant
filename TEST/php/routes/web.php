<?php
use App\Http\Controllers\LeaveController;

Route::get('/leaves', [LeaveController::class, 'index'])->name('leaves.index');
Route::get('/leaves/apply', [LeaveController::class, 'applyForm'])->name('leaves.applyForm');
Route::post('/leaves/apply', [LeaveController::class, 'apply'])->name('leaves.apply');
Route::post('/leaves/{id}/approve', [LeaveController::class, 'approve'])->name('leaves.approve');
Route::post('/leaves/{id}/reject', [LeaveController::class, 'reject'])->name('leaves.reject');
