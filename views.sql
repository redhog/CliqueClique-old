drop view if exists subscription_updates cascade;
drop view if exists subscription_deletes cascade;
drop view if exists subscription_changes cascade;
drop view if exists full_recursive_subscription cascade;
drop view if exists recursive_subscription cascade;
drop view if exists local_subscription cascade;
drop view if exists downstream_subscription cascade;
drop view if exists upstream_subscription cascade;
drop view if exists message_link cascade;


create view message_link as
  select
   link_message.node_id as node_id,
   link_message.src_message_id as src_message_id,
   link_message.message_id as dst_message_id
  from
   message as link_message,
   message as src_message
  where     link_message.src_message_id = src_message.message_id
        and link_message.node_id = src_message.node_id
 union
  select
   link_message.node_id as node_id,
   link_message.message_id as src_message_id,
   link_message.dst_message_id as dst_message_id
  from
   message as link_message,
   message as dst_message
  where     link_message.dst_message_id = dst_message.message_id
        and link_message.node_id = dst_message.node_id;

create view upstream_subscription as
 select
  node_id as node_id,
  message_id as message_id,
  peer_id as peer_id,

  local_is_subscribed as local_is_subscribed,
  local_center_node_is_subscribed as local_center_node_is_subscribed,
  local_center_node_id as local_center_node_id,
  local_center_distance as local_center_distance,

  remote_is_subscribed as remote_is_subscribed,
  remote_center_node_is_subscribed as remote_center_node_is_subscribed,
  remote_center_node_id as remote_center_node_id,
  remote_center_distance as remote_center_distance
 from
  subscription
 where
      local_is_subscribed is not null -- if the subscription is deleted
  and remote_is_subscribed is not null
  and (   local_center_node_is_subscribed < remote_center_node_is_subscribed
       or local_center_node_id > remote_center_node_id
       or local_center_distance > remote_center_distance
       or local_center_distance is null -- if the subscription is new
       or remote_center_distance is null);

create view downstream_subscription as
 select
  subscription.node_id as node_id,
  subscription.message_id as message_id,
  subscription.peer_id as peer_id,

  subscription.local_is_subscribed as local_is_subscribed,
  subscription.local_center_node_is_subscribed as local_center_node_is_subscribed,
  subscription.local_center_node_id as local_center_node_id,
  subscription.local_center_distance as local_center_distance,

  subscription.remote_is_subscribed as remote_is_subscribed,
  subscription.remote_center_node_is_subscribed as remote_center_node_is_subscribed,
  subscription.remote_center_node_id as remote_center_node_id,
  subscription.remote_center_distance as remote_center_distance
 from
  subscription
  join peer on
       subscription.node_id = peer.node_id
   and subscription.peer_id = peer.peer_id 
 where
     peer.do_mirror != 0
  or subscription.local_center_node_is_subscribed > subscription.remote_center_node_is_subscribed
  or subscription.local_center_node_id < subscription.remote_center_node_id
  or subscription.local_center_distance < subscription.remote_center_distance
  or subscription.local_center_distance is null
  or subscription.remote_center_distance is null;

create view local_subscription as
 select
  node_id as node_id,
  message_id as message_id,
  is_subscribed as is_subscribed,
  -min_center[1] as center_node_is_subscribed,
  min_center[2] as center_node_id,
  min_center[3] + 1 as center_distance
 from
  (select
    upstream.node_id as node_id,
    upstream.message_id as message_id,
    coalesce(
     max(
      case when upstream.local_center_distance is null or upstream.remote_center_distance is null then 0
      else downstream.remote_is_subscribed
      end),
     0) as is_subscribed,
    min(array[-upstream.remote_center_node_is_subscribed, upstream.remote_center_node_id, upstream.remote_center_distance]) as min_center
   from
    upstream_subscription as upstream

    join downstream_subscription as downstream on
	 upstream.node_id = downstream.node_id
     and upstream.message_id = downstream.message_id
   group by
    upstream.node_id,
    upstream.message_id
   having
    count(downstream.message_id) > 0) as multi_mini;

create view recursive_local_subscription as
 select
  message_link.node_id as node_id,
  message_link.dst_message_id as message_id,
 
  0 as is_subscribed,
  null as center_node_is_subscribed,
  null as center_node_id,
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
  max(center_node_is_subscribed) as center_node_is_subscribed,
  min(center_distance) as center_distance,
  min(center_node_id) as center_node_id -- could have done the min(array[]) thing here, but we're only ever gonna have two values, a value and null so it doesn't matter just here
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
  dst_subscription.local_center_node_is_subscribed as local_center_node_is_subscribed,
  dst_subscription.local_center_node_id as local_center_node_id,
  dst_subscription.local_center_distance as local_center_distance,

  dst_subscription.remote_is_subscribed as remote_is_subscribed,
  dst_subscription.remote_center_node_is_subscribed as remote_center_node_is_subscribed,
  dst_subscription.remote_center_node_id as remote_center_node_id,
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
create view subscription_changes as
 select
  full_recursive_local_subscription.node_id as node_id,
  full_recursive_local_subscription.message_id as message_id,
  full_recursive_subscription.peer_id as peer_id,

  full_recursive_local_subscription.is_subscribed as is_subscribed,
  full_recursive_local_subscription.center_node_is_subscribed as center_node_is_subscribed,
  full_recursive_local_subscription.center_node_id as center_node_id,
  full_recursive_local_subscription.center_distance as center_distance,

  -- If we don't have an existing subscription on record for the peer, send the whole message too 
  (full_recursive_subscription.remote_center_distance is null) as send_message
 from
  full_recursive_local_subscription
  join full_recursive_subscription on
       full_recursive_local_subscription.node_id = full_recursive_subscription.node_id
   and full_recursive_local_subscription.message_id = full_recursive_subscription.message_id
   and (   full_recursive_local_subscription.is_subscribed != full_recursive_subscription.local_is_subscribed
        or full_recursive_local_subscription.center_node_is_subscribed != full_recursive_subscription.local_center_node_is_subscribed
        or full_recursive_local_subscription.center_node_id != full_recursive_subscription.local_center_node_id
        or full_recursive_local_subscription.center_distance != full_recursive_subscription.local_center_distance
        or full_recursive_local_subscription.is_subscribed is null
        or full_recursive_subscription.local_is_subscribed is null
        or full_recursive_local_subscription.center_node_is_subscribed is null
        or full_recursive_subscription.local_center_node_is_subscribed is null
        or full_recursive_local_subscription.center_node_id is null
        or full_recursive_subscription.local_center_node_id is null
        or full_recursive_local_subscription.center_distance is null
        or full_recursive_subscription.local_center_distance is null);

-- Subscription to mark for removal
create view subscription_deletes as
 select
  subscription.node_id as node_id,
  subscription.message_id as message_id,
  subscription.peer_id as peer_id
 from
  subscription
 except
  select
   subscription.node_id as node_id,
   subscription.message_id as message_id,
   subscription.peer_id as peer_id
  from
   subscription
   join full_recursive_local_subscription on
	subscription.node_id = full_recursive_local_subscription.node_id
    and subscription.message_id = full_recursive_local_subscription.message_id;

-- Maybe some randomization of order here?
create view subscription_updates as
  select
   node_id as node_id,
   message_id as message_id,
   peer_id as peer_id,
   is_subscribed as is_subscribed,
   center_node_is_subscribed as center_node_is_subscribed,
   center_node_id as center_node_id,
   center_distance as center_distance,
   send_message as send_message,
   false as delete_subscription
  from subscription_changes
 union
  select
   node_id as node_id,
   message_id as message_id,
   peer_id as peer_id,
   null::integer as is_subscribed,
   null::integer  as center_node_is_subscribed,
   null::numeric as center_node_id,
   null::integer as center_distance,
   false as send_message,
   true as delete_subscription
  from subscription_deletes;
