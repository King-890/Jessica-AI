-- Enable RLS on the vector store table
alter table documents enable row level security;

-- Create policy to allow access to the 'brain'
-- (Adjust this for stricter security if you implement user-specific memory later)
create policy "Enable access to all users" 
on documents for all 
using (true) 
with check (true);
