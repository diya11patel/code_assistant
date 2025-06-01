<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Leave extends Model
{
    protected $fillable = ['employee_name', 'start_date', 'end_date', 'reason', 'status'];
}
