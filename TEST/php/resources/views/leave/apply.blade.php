<form action="{{ route('leaves.apply') }}" method="POST">
    @csrf
    <input name="employee_name" placeholder="Your name">
    <input type="date" name="start_date">
    <input type="date" name="end_date">
    <textarea name="reason" placeholder="Reason"></textarea>
    <button type="submit">Apply for Leave</button>
</form>
