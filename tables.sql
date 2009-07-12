drop table if exists annotations cascade;
drop table if exists subscription cascade;
drop table if exists message cascade;
drop table if exists peer cascade;


create table peer (
 node_id char (32),
 peer_id char (32),
 last_seen_time timestamp,
 last_seen_address varchar,
 do_mirror integer, -- not bool, to be able to do max(); 1 is true, 0 false
 primary key (node_id, peer_id)
);

create table message (
 node_id char (32),
 message_id char (32),
 message_challenge char (32), -- used to check if a peer has this message
 message_response char (32), -- reply from peer if it does have this message
 content varchar,
 src_message_id char (32), -- references message(message_id), but can point to unexistent rows
 dst_message_id char (32),
 primary key (node_id, message_id)
);

create table subscription (
 node_id char (32),
 message_id char (32),
 peer_id char (32),

 local_is_subscribed integer, -- not bool, to be able to do max(); 1 is true, 0 false, null is deleted
 local_center_distance integer,

 remote_is_subscribed integer, -- not bool, to be able to do max(); 1 is true, 0 false, null is deleted
 remote_center_distance integer,

 foreign key (node_id, message_id) references message(node_id, message_id),
 foreign key (node_id, peer_id) references peer(node_id, peer_id)
);

create table annotations (
 node_id char (32),
 message_id char (32), -- can be null to annotate the peer itself
 peer_id char (32),

 name varchar,
 value varchar,

 foreign key (node_id, message_id) references message(node_id, message_id),
 foreign key (node_id, peer_id) references peer(node_id, peer_id)
);
