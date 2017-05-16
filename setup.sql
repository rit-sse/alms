-- Funtion that notifies channel with json encoded data.
CREATE OR REPLACE FUNCTION table_change()
  RETURNS trigger AS
$BODY$declare
  result TEXT;
begin
  execute 'select row_to_json(' || TG_ARGV[0] || ') from ' || TG_ARGV[0] || ' where id=$1.id' into result using new;
	perform pg_notify(TG_ARGV[1], result);
	return new;
end
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
