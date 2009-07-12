drop view if exists subscription_updates cascade;
drop view if exists full_recursive_subscription cascade;
drop view if exists recursive_subscription cascade;
drop view if exists local_subscription cascade;
drop view if exists message_link cascade;


create view message_link as
  select
   node_id as node_id,
   src_message_id as src_message_id,
   message_id as dst_message_id
  from
   message
  where src_message_id is not null
 union
  select
   node_id as node_id,
   message_id as src_message_id,
   dst_message_id as dst_message_id
  from
   message
  where dst_message_id is not null;

create view local_subscription as
 select
  upstream.node_id as node_id,
  upstream.message_id as message_id,
  coalesce(
   max(
    case when upstream.local_center_distance is null or upstream.remote_center_distance is null then 0
    else downstream.remote_is_subscribed
    end),
   0) as is_subscribed,
  min(upstream.remote_center_distance) + 1 as center_distance
 from
  subscription as upstream

  join peer as upstream_peer on
       upstream.local_center_distance is not NULL
       upstream.node_id = upstream_peer.node_id 
   and upstream.peer_id = upstream_peer.peer_id
   and (   upstream.local_center_distance > upstream.remote_center_distance
        or upstream.local_center_distance is null
        or upstream.remote_center_distance is null)

  join subscription as downstream on
       upstream.node_id = downstream.node_id

  join peer as downstream_peer on
       downstream.node_id = downstream_peer.node_id
   and downstream.peer_id = downstream_peer.peer_id 
   and (   downstream_peer.do_mirror != 0
        or downstream.local_center_distance <= downstream.remote_center_distance
        or downstream.local_center_distance is null
        or downstream.remote_center_distance is null)
   and upstream.message_id = downstream.message_id
 group by
  upstream.node_id,
  upstream.message_id
 having
  count(downstream.message_id) > 0;

create view recursive_local_subscription as
 select
  message_link.node_id as node_id,
  message_link.dst_message_id as message_id,
 
  0 as is_subscribed,
  null as center_distance
 from
  message_link
  join local_subscription as src_subscription on
       src_subscription.node_id = message_link.node_id
   and message_link.src_message_id = src_subscription.message_id
   and src_subscription.is_subscribed != 0;

create view full_recursive_local_subscription as
 select
  node_id,
  message_id,
  max(is_subscribed) as is_subscribed,
  min(center_distance) as center_distance
 from
  (      select * from recursive_local_subscription
   union select * from local_subscription) as s
 group by
  node_id,
  message_id;

create view recursive_subscription as
 select
  message_link.node_id as node_id,
  message_link.dst_message_id as message_id,
  src_subscription.peer_id as peer_id,

  dst_subscription.local_is_subscribed as local_is_subscribed,
  dst_subscription.local_center_distance as local_center_distance,

  dst_subscription.remote_is_subscribed as remote_is_subscribed,
  dst_subscription.remote_center_distance as remote_center_distance
 from
  message_link
  join subscription as src_subscription on
       src_subscription.node_id = message_link.node_id
   and message_link.src_message_id = src_subscription.message_id
   and src_subscription.remote_is_subscribed != 0
  left outer join subscription as dst_subscription on
       message_link.node_id = dst_subscription.node_id
   and message_link.dst_message_id = dst_subscription.message_id
   and src_subscription.peer_id = dst_subscription.peer_id;

create view full_recursive_subscription as
 select distinct * from
  (      select * from recursive_subscription
   union select * from subscription) as s;

-- Difference between what other peers know of our subscription and our current subscription
create view subscription_updates as
 select
  full_recursive_local_subscription.node_id as node_id,
  full_recursive_local_subscription.message_id as message_id,
  full_recursive_subscription.peer_id as peer_id,

  full_recursive_local_subscription.is_subscribed as is_subscribed,
  full_recursive_local_subscription.center_distance as center_distance,

  -- If we don't have an existing subscription on record for the peer, send the whole message too 
  (full_recursive_subscription.remote_center_distance is null) as send_message
 from
  full_recursive_local_subscription
  join full_recursive_subscription on
       full_recursive_local_subscription.node_id = full_recursive_subscription.node_id
   and full_recursive_local_subscription.message_id = full_recursive_subscription.message_id
   and (   full_recursive_local_subscription.is_subscribed != full_recursive_subscription.local_is_subscribed
        or full_recursive_local_subscription.center_distance != full_recursive_subscription.local_center_distance
        or full_recursive_local_subscription.is_subscribed is null
        or full_recursive_subscription.local_is_subscribed is null
        or full_recursive_local_subscription.center_distance is null
        or full_recursive_subscription.local_center_distance is null)
 -- Subscription to mark for removal
 union
 (select
   subscription.node_id as node_id,
   subscription.message_id as message_id,
   subscription.peer_id as peer_id,
   null::integer as is_subscribed,
   null::integer as center_distance,
   false::bool as send_message
  from
   subscription
  except
   select
    subscription.node_id as node_id,
    subscription.message_id as message_id,
    subscription.peer_id as peer_id,
    null::integer as is_subscribed,
    null::integer as center_distance,
    false::bool as send_message
   from
    subscription
    join full_recursive_local_subscription on
	 subscription.node_id = full_recursive_local_subscription.node_id
     and subscription.message_id = full_recursive_local_subscription.message_id);
