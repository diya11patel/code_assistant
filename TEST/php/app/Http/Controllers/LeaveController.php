<?php
namespace App\Http\Controllers;

use App\Models\Leave;
use Illuminate\Http\Request;

class LeaveController extends Controller
{
    public function index() {
        return view('leave.index', ['leaves' => Leave::all()]);
    }

    public function applyForm() {
        return view('leave.apply');
    }

    public function apply(Request $request) {
        Leave::create($request->all());
        return redirect()->route('leaves.index');
    }

    public function approve($id) {
        $leave = Leave::findOrFail($id);
        $leave->status = 'approved';
        $leave->save();
        return back();
    }

    public function reject($id) {
        $leave = Leave::findOrFail($id);
        $leave->status = 'rejected';
        $leave->save();
        return back();
    }
}
