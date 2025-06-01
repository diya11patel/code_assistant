<h1>All Leave Applications</h1>
@foreach($leaves as $leave)
    <p>{{ $leave->employee_name }} | {{ $leave->start_date }} to {{ $leave->end_date }} | {{ $leave->status }}</p>
    <form method="POST" action="{{ route('leaves.approve', $leave->id) }}">@csrf<button>Approve</button></form>
    <form method="POST" action="{{ route('leaves.reject', $leave->id) }}">@csrf<button>Reject</button></form>
@endforeach
