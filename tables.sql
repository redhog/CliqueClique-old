drop table if exists annotations cascade;
drop table if exists subscription cascade;
drop table if exists message cascade;
drop table if exists peer cascade;


create table peer (
 node_id numeric,
 peer_id numeric,
 last_seen_time timestamp,
 last_seen_address varchar,
 do_mirror integer, -- not bool, to be able to do max(); 1 is true, 0 false
 primary key (node_id, peer_id)
);

create table message (
 node_id numeric,
 message_id numeric,
 message_challenge numeric, -- used to check if a peer has this message
 message_response numeric, -- reply from peer if it does have this message
 content varchar,
 src_message_id numeric, -- references message(message_id), but can point to unexistent rows
 dst_message_id numeric,
 primary key (node_id, message_id)
);

create table subscription (
 node_id numeric,
 message_id numeric,
 peer_id numeric,

 local_is_subscribed integer, -- not bool, to be able to do max(); 1 is true, 0 false, null is deleted
 local_center_node numeric,
 local_center_distance integer,

 remote_is_subscribed integer, -- not bool, to be able to do max(); 1 is true, 0 false, null is deleted
 remote_center_node numeric,
 remote_center_distance integer,

 foreign key (node_id, message_id) references message(node_id, message_id),
 foreign key (node_id, peer_id) references peer(node_id, peer_id)
);

create table annotations (
 node_id numeric,
 message_id numeric, -- can be null to annotate the peer itself
 peer_id numeric,

 name varchar,
 value varchar,

 foreign key (node_id, message_id) references message(node_id, message_id),
 foreign key (node_id, peer_id) references peer(node_id, peer_id)
);
