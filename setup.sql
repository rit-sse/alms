
-- Funtion that notifies channel with json encoded event data.
CREATE OR REPLACE FUNCTION event_change()
  RETURNS trigger AS
$BODY$declare
	event TEXT;
begin
	select row_to_json(events) into event from events where id=new.id;
	perform pg_notify('ssevents', event);
	return new;
end
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

-- Setup the trigger on events
drop trigger if exists event_after on events;
create trigger event_after
    after insert or update
on events
for each row
    execute procedure event_change();
