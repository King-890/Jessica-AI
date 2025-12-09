-- Create buckets if they don't exist
insert into storage.buckets (id, name, public)
values 
  ('models', 'models', true),
  ('datasets', 'datasets', true)
on conflict (id) do nothing;

-- Allow public access to 'models' bucket
create policy "Public Access to Models"
  on storage.objects for select
  using ( bucket_id = 'models' );

create policy "Allow Uploads to Models"
  on storage.objects for insert
  with check ( bucket_id = 'models' );

create policy "Allow Updates to Models"
  on storage.objects for update
  using ( bucket_id = 'models' );

-- Allow public access to 'datasets' bucket
create policy "Public Access to Datasets"
  on storage.objects for select
  using ( bucket_id = 'datasets' );

create policy "Allow Uploads to Datasets"
  on storage.objects for insert
  with check ( bucket_id = 'datasets' );
