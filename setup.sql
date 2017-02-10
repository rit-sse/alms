
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

-- Setup the triggers
drop trigger if exists event_after on events;
drop trigger if exists quote_after on quotes;
drop trigger if exists membership_after on memberships;

create trigger event_after
    after insert or update
on events
for each row
    execute procedure table_change('events', 'ssevents');

create trigger quote_after
    after insert
on quotes
for each row
    execute procedure table_change('quotes', 'ssequotes');

create trigger membership_after
    after insert
on memberships
for each row
    execute procedure table_change('memberships', 'ssememberships');

