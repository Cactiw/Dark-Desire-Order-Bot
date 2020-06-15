create table bot_updates
(
    update_id    serial not null
        constraint bot_updates_pkey
            primary key,
    text         varchar,
    date_created timestamp
);

alter table bot_updates
    owner to admin;

create table deferred_orders
(
    deferred_id serial not null
        constraint deferred_orders_pkey
            primary key,
    order_id    integer,
    time_set    timestamp,
    target      integer,
    defense     integer,
    tactics     varchar(128),
    divisions   boolean[],
    potions     boolean[]
);

alter table deferred_orders
    owner to admin;

create table guilds
(
    guild_id             serial      not null
        constraint guilds_pkey
            primary key,
    guild_tag            varchar(10) not null,
    guild_name           varchar(16),
    chat_id              bigint,
    members              integer[],
    commander_id         integer,
    division             varchar(10) default 'Запад'::character varying,
    chat_name            varchar(256),
    invite_link          varchar(24),
    orders_enabled       boolean     default true,
    pin_enabled          boolean     default true,
    disable_notification boolean     default false,
    assistants           integer[],
    settings             json,
    api_info             json,
    mailing_enabled      boolean     default true,
    last_updated         timestamp,
    castle               varchar     default ''::character varying,
    alliance_id          integer
);

alter table guilds
    owner to admin;

create table locations
(
    location_id      integer not null
        constraint locations_pkey
            primary key,
    state            boolean default true,
    building_process bigint  default '-1'::integer,
    special_info     json
);

alter table locations
    owner to admin;

create table mobs
(
    link           varchar not null
        constraint mobs_pkey
            primary key,
    mob_names      character varying[],
    mob_lvls       integer[],
    date_created   timestamp,
    created_player integer,
    on_channel     boolean             default false,
    helpers        character varying[] default ARRAY []::character varying[],
    buffs          character varying[] default ARRAY []::character varying[],
    minutes        integer             default 3
);

alter table mobs
    owner to admin;

create table players
(
    id              integer not null
        constraint players_pkey
            primary key,
    username        varchar(32),
    nickname        varchar(32),
    guild_tag       varchar(10),
    guild           integer
        constraint players_guild_fkey
            references guilds,
    lvl             integer not null,
    attack          integer not null,
    defense         integer not null,
    stamina         integer not null,
    pet             varchar(48),
    equipment       json,
    game_class      varchar(12) default NULL::character varying,
    class_skill_lvl integer,
    castle          varchar(3)  default '🖤'::character varying,
    last_updated    timestamp,
    reputation      integer     default 0,
    created         timestamp,
    status          integer,
    guild_history   integer[],
    exp             integer,
    api_info        json,
    stock           json,
    settings        json,
    exp_info        json,
    class_info      json,
    mobs_info       json,
    ach_info        json,
    tea_party_info  json,
    quests_info     json,
    hp              integer,
    max_hp          integer,
    pogs            integer
);

alter table players
    owner to admin;

create table castle_logs
(
    log_id          serial  not null
        constraint castle_logs_pkey
            primary key,
    player_id       integer
        constraint castle_logs_player_id_fkey
            references players,
    action          varchar not null,
    result          integer,
    date            timestamp,
    additional_info json
);

alter table castle_logs
    owner to admin;

create table king_audiences
(
    audience_id       serial not null
        constraint king_audiences_pkey
            primary key,
    request_player_id integer
        constraint king_audiences_request_player_id_fkey
            references players,
    king_player_id    integer
        constraint king_audiences_king_player_id_fkey
            references players,
    date_created      timestamp,
    date_accepted     timestamp,
    accepted          boolean
);

alter table king_audiences
    owner to admin;

create table mob_reports
(
    report_id          serial not null
        constraint mob_reports_pkey
            primary key,
    player_id          integer
        constraint mob_reports_player_id_fkey
            references players,
    attack             integer,
    additional_attack  integer,
    defense            integer,
    additional_defense integer,
    lvl                integer,
    exp                integer,
    gold               integer,
    stock              integer,
    mob_names          character varying[],
    mob_lvls           integer[],
    buffs              character varying[],
    hp                 integer,
    hit                integer,
    miss               integer,
    last_hit           integer,
    date_created       timestamp
);

alter table mob_reports
    owner to admin;

create table reports
(
    report_id          serial  not null
        constraint reports_pkey
            primary key,
    player_id          integer not null
        constraint reports_player_id_fkey
            references players,
    battle_id          integer not null,
    attack             integer,
    additional_attack  integer,
    defense            integer,
    additional_defense integer,
    lvl                integer,
    exp                integer,
    gold               integer,
    stock              integer,
    equip              json,
    outplay            json
);

alter table reports
    owner to admin;

create table trade_unions
(
    id         serial not null
        constraint trade_unions_pkey
            primary key,
    creator_id integer,
    name       varchar(64),
    players    integer[],
    view_link  varchar(32),
    chat_id    bigint,
    assistants integer[] default ARRAY []::integer[]
);

alter table trade_unions
    owner to admin;

create table triggers
(
    text_in      varchar(4096) not null,
    type         integer       not null,
    data_out     varchar(4096) not null,
    chat_id      bigint        not null,
    creator      varchar(64),
    date_created timestamp
);

alter table triggers
    owner to admin;

create table votes
(
    id       serial  not null
        constraint votes_pkey
            primary key,
    name     varchar not null,
    text     varchar,
    variants character varying[],
    choices  json,
    started  timestamp,
    duration interval,
    classes  boolean[] default ARRAY []::boolean[]
);

alter table votes
    owner to admin;

create table worldtop
(
    battle_id integer not null
        constraint worldtop_pkey
            primary key,
    tortuga   integer,
    rassvet   integer,
    ferma     integer,
    oplot     integer,
    night     integer,
    amber     integer,
    skala     integer
);

alter table worldtop
    owner to admin;

create table alliances
(
    id         serial  not null
        constraint alliances_pkey
            primary key,
    link       varchar,
    name       varchar not null,
    creator_id integer
        constraint alliances_creator_id_fkey
            references players,
    assistants integer[],
    hq_chat_id bigint
);

alter table alliances
    owner to admin;

alter table guilds
    add constraint guilds_alliance_id_fk
        foreign key (alliance_id) references alliances
            on update cascade on delete set null;

create table alliance_locations
(
    id          serial  not null
        constraint alliance_locations_pkey
            primary key,
    link        varchar,
    name        varchar not null,
    type        varchar,
    lvl         integer,
    owner_id    integer
        constraint alliance_locations_owner_id_fkey
            references alliances,
    turns_owned integer default 0,
    can_expired boolean default false,
    expired     boolean default false
);

alter table alliance_locations
    owner to admin;
    
create table shops (
    id serial primary key,
    link varchar,
    name varchar,
    ownerTag varchar,
    ownerName varchar,
    ownerCastle varchar,
    kind varchar,
    mana int,
    offers json,
    specialization json,
    qualityCraftLevel int,
    maintenanceEnabled bool,
    maintenanceCost int,
    guildDiscount int,
    castleDiscount int,

    last_seen timestamp

);

alter table shops
    owner to admin;
    
