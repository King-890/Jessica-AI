-- Allow ALL operations for public (since we want to upload/update freely for now)
-- You can restrict this later if needed.

-- Policices for 'datasets'
drop policy if exists "Allow Uploads to Datasets" on storage.objects;
drop policy if exists "Allow Updates to Datasets" on storage.objects;

create policy "Allow Uploads to Datasets"
  on storage.objects for insert
  with check ( bucket_id = 'datasets' );

create policy "Allow Updates to Datasets"
  on storage.objects for update
  using ( bucket_id = 'datasets' );

-- Policies for 'models'
drop policy if exists "Allow Uploads to Models" on storage.objects;
drop policy if exists "Allow Updates to Models" on storage.objects;

create policy "Allow Uploads to Models"
  on storage.objects for insert
  with check ( bucket_id = 'models' );

create policy "Allow Updates to Models"
  on storage.objects for update
  using ( bucket_id = 'models' );
