--
-- PostgreSQL database dump
--

\restrict fdwYrIvchWikEY9wR6Dg5H6c3n9g7Qoo6rY4d5pIA56KKUlypEzptD6nOW4WbPx

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_timestamp_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_timestamp_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN NEW.update_time = now(); RETURN NEW; END; $$;


--
-- Name: update_update_time(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_update_time() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.update_time := CURRENT_TIMESTAMP(3);
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_attachments (
    id bigint NOT NULL,
    uuid uuid DEFAULT gen_random_uuid() NOT NULL,
    lead_id bigint,
    form_code character varying(32) NOT NULL,
    original_name character varying(255) NOT NULL,
    file_ext character varying(20) DEFAULT NULL::character varying,
    mime_type character varying(150) NOT NULL,
    file_size bigint NOT NULL,
    file_index smallint DEFAULT 1 NOT NULL,
    storage_key character varying(500) NOT NULL,
    upload_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    uploaded_at timestamp(3) with time zone DEFAULT NULL::timestamp with time zone,
    create_by bigint DEFAULT 0 NOT NULL,
    update_by bigint DEFAULT 0 NOT NULL,
    delete_by bigint,
    create_time timestamp(3) with time zone DEFAULT CURRENT_TIMESTAMP(3) NOT NULL,
    update_time timestamp(3) with time zone DEFAULT CURRENT_TIMESTAMP(3) NOT NULL,
    delete_time timestamp(3) with time zone DEFAULT NULL::timestamp with time zone,
    is_deleted smallint DEFAULT 0 NOT NULL,
    remark character varying(500) DEFAULT NULL::character varying,
    CONSTRAINT form_attachments_file_index_check CHECK ((file_index > 0)),
    CONSTRAINT form_attachments_file_size_check CHECK ((file_size > 0)),
    CONSTRAINT form_attachments_is_deleted_check CHECK ((is_deleted = ANY (ARRAY[0, 1]))),
    CONSTRAINT form_attachments_storage_key_check CHECK ((((storage_key)::text !~ '^[/\\]'::text) AND ((storage_key)::text !~ '^[A-Za-z]:'::text) AND ((storage_key)::text !~ '^(file|http|https):'::text) AND ((storage_key)::text !~~ '%..%'::text)))
);


--
-- Name: TABLE form_attachments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.form_attachments IS '表单附件：F03/F04/F05/F06 上传元数据与受控存储路径';


--
-- Name: COLUMN form_attachments.uuid; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.uuid IS '外部唯一标识（同时作为存储文件名）';


--
-- Name: COLUMN form_attachments.lead_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.lead_id IS '归属线索；上传阶段为空，表单提交后回填';


--
-- Name: COLUMN form_attachments.form_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.form_code IS '表单编码：F03 / F04 / F05 / F06';


--
-- Name: COLUMN form_attachments.original_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.original_name IS '用户原始文件名（仅展示）';


--
-- Name: COLUMN form_attachments.file_ext; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.file_ext IS '小写扩展名，如 jpg / png / pdf / step / stl / ai';


--
-- Name: COLUMN form_attachments.mime_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.mime_type IS '服务端识别的 MIME 类型';


--
-- Name: COLUMN form_attachments.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.file_size IS '文件大小（字节），服务端二次校验上限';


--
-- Name: COLUMN form_attachments.file_index; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.file_index IS '同一线索内的文件序号（1 起）';


--
-- Name: COLUMN form_attachments.storage_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.storage_key IS '受控存储相对路径：{form_code}/{YYYYMMDD}/{uuid}.{ext}，不含盘符或服务器绝对路径';


--
-- Name: COLUMN form_attachments.upload_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.upload_status IS '上传状态，取值由业务确认（默认 pending）';


--
-- Name: COLUMN form_attachments.uploaded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.uploaded_at IS '上传完成时间';


--
-- Name: COLUMN form_attachments.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.create_by IS '创建人ID';


--
-- Name: COLUMN form_attachments.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.update_by IS '更新人ID';


--
-- Name: COLUMN form_attachments.delete_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.delete_by IS '删除人ID';


--
-- Name: COLUMN form_attachments.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.create_time IS '创建时间';


--
-- Name: COLUMN form_attachments.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.update_time IS '更新时间';


--
-- Name: COLUMN form_attachments.delete_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.delete_time IS '删除时间';


--
-- Name: COLUMN form_attachments.is_deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.is_deleted IS '逻辑删除标志：0 正常 / 1 已删除';


--
-- Name: COLUMN form_attachments.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.form_attachments.remark IS '备注';


--
-- Name: form_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.form_attachments ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.form_attachments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_attachment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_attachment (
    id bigint NOT NULL,
    filename character varying(255) NOT NULL,
    storage_path character varying(500) NOT NULL,
    file_size bigint NOT NULL,
    file_type character varying(100) NOT NULL,
    upload_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    upload_user_id bigint NOT NULL,
    description text,
    access_permission character varying(10) DEFAULT 'private'::character varying NOT NULL,
    status character varying(10) DEFAULT 'normal'::character varying NOT NULL,
    module character varying(50),
    data_id uuid DEFAULT gen_random_uuid(),
    title character varying(255),
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    delete_by bigint DEFAULT 0,
    delete_time timestamp without time zone,
    is_deleted smallint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    remark text
);


--
-- Name: x_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_attachment ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_demo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_demo (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    name character varying(255) NOT NULL,
    description text,
    sort integer DEFAULT 0,
    status smallint DEFAULT 1,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_demo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_demo ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_demo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_dept; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_dept (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    title character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    pid bigint,
    sort integer DEFAULT 0,
    status smallint DEFAULT 1,
    description text,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_dept_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_dept ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_dept_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_log (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    level character varying(16) NOT NULL,
    logger character varying(128),
    module character varying(128),
    func character varying(128),
    line integer,
    message text,
    exc_info text,
    request_id character varying(64),
    request_path character varying(255),
    request_method character varying(16),
    client_ip character varying(64),
    user_id bigint,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    remark text
);


--
-- Name: x_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.x_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: x_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.x_log_id_seq OWNED BY public.x_log.id;


--
-- Name: x_menu; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_menu (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    title character varying(255) NOT NULL,
    name character varying(100) NOT NULL,
    pid bigint,
    path character varying(255),
    component character varying(255),
    icon character varying(50),
    sort integer DEFAULT 0,
    type smallint DEFAULT 1,
    permission character varying(100),
    status smallint DEFAULT 1,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_menu_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_menu ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_menu_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_notification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_notification (
    id bigint NOT NULL,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    type character varying(50) NOT NULL,
    subtype character varying(50),
    download_url character varying(255),
    read boolean DEFAULT false,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data_id uuid DEFAULT gen_random_uuid(),
    status smallint DEFAULT 1,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    create_by bigint DEFAULT 0,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_by bigint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    is_deleted smallint DEFAULT 0,
    remark text
);


--
-- Name: x_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_notification ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    pid bigint DEFAULT 0,
    title character varying(100) NOT NULL,
    code character varying(100) NOT NULL,
    module character varying(50),
    type smallint DEFAULT 2,
    path character varying(200),
    icon character varying(100),
    sort integer DEFAULT 0,
    status smallint DEFAULT 1,
    description character varying(255),
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission_group (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    code character varying(100) NOT NULL,
    title character varying(100) NOT NULL,
    menu_id bigint DEFAULT 0,
    module character varying(50),
    sort integer DEFAULT 0,
    status smallint DEFAULT 1,
    description character varying(255),
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission_group_data (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    group_id bigint NOT NULL,
    module character varying(50) NOT NULL,
    scope character varying(20) DEFAULT 'dept'::character varying,
    custom_dept_ids jsonb DEFAULT '[]'::jsonb,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission_group_data ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_group_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission_group_field; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission_group_field (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    group_id bigint NOT NULL,
    module character varying(50) NOT NULL,
    field character varying(100) NOT NULL,
    field_label character varying(100),
    visible smallint DEFAULT 1,
    editable smallint DEFAULT 1,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group_field_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission_group_field ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_group_field_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission_group ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission_group_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission_group_permission (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    group_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission_group_permission ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_group_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission_group_subject; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_permission_group_subject (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    group_id bigint NOT NULL,
    subject_type character varying(10) NOT NULL,
    subject_id bigint NOT NULL,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_permission_group_subject_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission_group_subject ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_group_subject_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_permission ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_role (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    title character varying(255) NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(100) NOT NULL,
    description text,
    status smallint DEFAULT 1,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_role ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_role_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_role_permission (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_role_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_role_permission ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_role_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_user (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    title character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    name character varying(100) NOT NULL,
    phone character varying(20),
    email character varying(100),
    dept_id bigint,
    avatar character varying(255),
    status smallint DEFAULT 1,
    last_login_time timestamp without time zone,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    token character varying(255) DEFAULT 'default_token'::character varying NOT NULL,
    image_path character varying(500),
    attachment_ids text,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: COLUMN x_user.image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.x_user.image_path IS '用户图片路径';


--
-- Name: COLUMN x_user.attachment_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.x_user.attachment_ids IS '用户附件ID列表，逗号分隔';


--
-- Name: x_user_api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_user_api_key (
    id bigint NOT NULL,
    user_id integer DEFAULT 1 NOT NULL,
    name character varying(255),
    key character varying(255),
    status smallint DEFAULT 1,
    description text,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expire_time timestamp without time zone,
    data_id uuid DEFAULT gen_random_uuid(),
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    delete_by bigint DEFAULT 0,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    delete_time timestamp without time zone,
    is_deleted smallint DEFAULT 0,
    remark text
);


--
-- Name: x_user_api_key_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.x_user_api_key_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: x_user_api_key_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.x_user_api_key_id_seq OWNED BY public.x_user_api_key.id;


--
-- Name: x_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_user ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_user_login; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_user_login (
    id bigint NOT NULL,
    user_id integer DEFAULT 1 NOT NULL,
    ip character varying(50),
    user_agent text,
    login_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'success'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data_id uuid DEFAULT gen_random_uuid(),
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    delete_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    delete_time timestamp without time zone,
    is_deleted smallint DEFAULT 0,
    remark text
);


--
-- Name: x_user_login_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.x_user_login_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: x_user_login_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.x_user_login_id_seq OWNED BY public.x_user_login.id;


--
-- Name: x_user_permission_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_user_permission_group (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    user_id bigint NOT NULL,
    group_id bigint NOT NULL,
    is_active smallint DEFAULT 0,
    activate_time timestamp without time zone,
    create_by bigint DEFAULT 0,
    update_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted smallint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    remark text
);


--
-- Name: x_user_permission_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_user_permission_group ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_user_permission_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.x_user_role (
    id bigint NOT NULL,
    data_id uuid DEFAULT gen_random_uuid(),
    user_id bigint,
    role_id bigint,
    create_by bigint DEFAULT 0,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    title character varying(255),
    status smallint DEFAULT 1,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_by bigint DEFAULT 0,
    delete_time timestamp without time zone,
    delete_by bigint DEFAULT 0,
    is_deleted smallint DEFAULT 0,
    remark text
);


--
-- Name: x_user_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.x_user_role ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.x_user_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: x_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_log ALTER COLUMN id SET DEFAULT nextval('public.x_log_id_seq'::regclass);


--
-- Name: x_user_api_key id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_api_key ALTER COLUMN id SET DEFAULT nextval('public.x_user_api_key_id_seq'::regclass);


--
-- Name: x_user_login id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_login ALTER COLUMN id SET DEFAULT nextval('public.x_user_login_id_seq'::regclass);


--
-- Data for Name: form_attachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.form_attachments (id, uuid, lead_id, form_code, original_name, file_ext, mime_type, file_size, file_index, storage_key, upload_status, uploaded_at, create_by, update_by, delete_by, create_time, update_time, delete_time, is_deleted, remark) FROM stdin;
25	76ba906f-dd99-4f5f-a02e-dadd12da328a	\N	F03	jt-ref.png	png	image/png	64	1	F03/20261105/ae71b4c6ab67443ba5c2b7470e13d4b2.png	uploaded	2026-11-05 09:20:18.362+08	0	0	\N	2026-11-05 09:20:18.362+08	2026-11-05 09:20:18.362+08	\N	0	\N
26	c211e967-2568-4bb7-a7fd-ade999214d7a	\N	F03	jt-reference.png	png	image/png	4	1	F03/20261105/be9ef5539deb4ad5b4fb01d5692f7e9d.png	uploaded	2026-11-05 10:22:23.859+08	0	0	\N	2026-11-05 10:22:23.859+08	2026-11-05 10:22:23.859+08	\N	0	\N
27	481b1832-fc58-4060-a730-b2effeed61bb	\N	F03	jt-ref.png	png	image/png	4	1	F03/20261105/43b8d4fb676847a1b13e70a06708f10b.png	uploaded	2026-11-05 10:23:14.643+08	0	0	\N	2026-11-05 10:23:14.643+08	2026-11-05 10:23:14.643+08	\N	0	\N
28	7896f7b0-c5bb-4d99-9a67-edf522b815fd	\N	F03	jt-reference.png	png	image/png	4	1	F03/20261105/aeac9b7c2d4647cd9d7d7816d2c51e7e.png	uploaded	2026-11-05 10:23:31.251+08	0	0	\N	2026-11-05 10:23:31.251+08	2026-11-05 10:23:31.251+08	\N	0	\N
29	2516193a-a204-46b7-a202-00366de3f913	\N	F03	jt-reference.png	png	image/png	4	1	F03/20261105/cc950ba9ff66468c8fe1eb0044a4c0bb.png	uploaded	2026-11-05 10:23:58.885+08	0	0	\N	2026-11-05 10:23:58.885+08	2026-11-05 10:23:58.885+08	\N	0	\N
30	ed539f63-11ff-47ec-8357-2b9c7c4afa9c	119	F03	jt-reference.png	png	image/png	4	1	F03/20261105/c5e64e20683d4743a02424508a3e0da4.png	uploaded	2026-11-05 10:24:19.395+08	0	0	\N	2026-11-05 10:24:19.395+08	2026-11-05 10:24:19.445+08	\N	0	\N
31	390bbad1-0fab-44e0-8edc-9993e8ea86a5	125	F03	jt-reference.png	png	image/png	4	1	F03/20261105/e10c01df74414e4aa46f092cdb86d5a1.png	uploaded	2026-11-05 10:24:49.413+08	0	0	\N	2026-11-05 10:24:49.413+08	2026-11-05 10:24:49.472+08	\N	0	\N
32	2a73b7cb-fbdf-4e4d-8f15-efdfdc5c08c0	129	F03	jt-retry.png	png	image/png	3	1	F03/20261105/63d66dcde4e248a393e95ef66f293d4e.png	uploaded	2026-11-05 10:25:10.873+08	0	0	\N	2026-11-05 10:25:10.873+08	2026-11-05 10:25:10.939+08	\N	0	\N
33	fe36e5bf-dea4-420d-82b3-5459877eea37	134	F03	jt-reference.png	png	image/png	4	1	F03/20261105/845b0e43edfe49f2b4250e752e355a33.png	uploaded	2026-11-05 11:12:27.008+08	0	0	\N	2026-11-05 11:12:27.008+08	2026-11-05 11:12:27.1+08	\N	0	\N
34	4893e0e8-9f91-4ce7-b695-a8b04c02d5fb	140	F03	jt-retry.png	png	image/png	3	1	F03/20261105/0da255305cab4c869391123943e15fa6.png	uploaded	2026-11-05 11:12:44.83+08	0	0	\N	2026-11-05 11:12:44.83+08	2026-11-05 11:12:44.91+08	\N	0	\N
36	26e4fb28-8f02-44d7-bb7e-c11f7b62d2b9	159	F06	jt6.png	png	image/png	8	1	F06/20261105/dfdafe02ad1a42df93ef70ccd2e00aed.png	uploaded	2026-11-05 11:40:39.835+08	0	0	\N	2026-11-05 11:40:39.835+08	2026-11-05 11:40:39.848+08	\N	0	\N
39	d46fd83e-5489-4fc8-b033-d35c62dd1c21	173	F03	jt-reference.png	png	image/png	4	1	F03/20261105/bcf2d7b8d0564cff8e6cdd17e5871294.png	uploaded	2026-11-05 12:48:22.118+08	0	0	\N	2026-11-05 12:48:22.118+08	2026-11-05 12:48:22.178+08	\N	0	\N
40	4992b0f9-c994-4393-a396-19335e5b9bf9	179	F03	jt-retry.png	png	image/png	3	1	F03/20261105/648ddc438ce44042824598660ad6827c.png	uploaded	2026-11-05 12:48:37.708+08	0	0	\N	2026-11-05 12:48:37.708+08	2026-11-05 12:48:37.776+08	\N	0	\N
41	e83ae85f-1137-4030-85bf-e0e02259c197	181	F03	jt-reference.png	png	image/png	4	1	F03/20261105/896694d46c79486ba20d5667aa6eaf8a.png	uploaded	2026-11-05 12:59:43.282+08	0	0	\N	2026-11-05 12:59:43.282+08	2026-11-05 12:59:43.35+08	\N	0	\N
42	abc786e8-b764-4c2b-8661-51ef3bd21edb	187	F03	jt-retry.png	png	image/png	3	1	F03/20261105/33d9ebc5afc84eb59ff1b4214a3ebbae.png	uploaded	2026-11-05 13:00:00.808+08	0	0	\N	2026-11-05 13:00:00.808+08	2026-11-05 13:00:00.895+08	\N	0	\N
43	2f09a3ea-6db0-40e8-91f5-3d7bc57fe135	190	F03	jt-reference.png	png	image/png	4	1	F03/20261105/0864f825c2eb416cbc7ce30628496af5.png	uploaded	2026-11-05 13:10:17.324+08	0	0	\N	2026-11-05 13:10:17.324+08	2026-11-05 13:10:17.368+08	\N	0	\N
44	67b8ea77-bdd9-4c21-9a56-fcdc770ba5a7	196	F03	jt-retry.png	png	image/png	3	1	F03/20261105/b904b217bcc44ee5a9716a4f78c4cc03.png	uploaded	2026-11-05 13:10:32.449+08	0	0	\N	2026-11-05 13:10:32.449+08	2026-11-05 13:10:32.52+08	\N	0	\N
\.


--
-- Data for Name: x_attachment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_attachment (id, filename, storage_path, file_size, file_type, upload_time, upload_user_id, description, access_permission, status, module, data_id, title, create_by, update_by, delete_by, delete_time, is_deleted, create_time, update_time, remark) FROM stdin;
\.


--
-- Data for Name: x_demo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_demo (id, data_id, name, description, sort, status, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_dept; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_dept (id, data_id, title, name, code, pid, sort, status, description, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_log (id, data_id, level, logger, module, func, line, message, exc_info, request_id, request_path, request_method, client_ip, user_id, create_time, is_deleted, delete_time, delete_by, create_by, update_by, update_time, remark) FROM stdin;
17	13447c08-5a1c-4359-865e-44fc270cd2e4	INFO	framework.core.config	config	_load_config	125	开始加载配置文件...	\N	1556daefb8514187	/admin/auth/login	POST	127.0.0.1	\N	2026-11-06 17:27:18.666915	0	\N	0	0	0	2026-11-07 01:27:18.671299	\N
18	602b9ec2-1392-411f-b909-74a4af9899c3	INFO	framework.core.config	config	_load_env_file	68	加载 .env 文件: C:\\1.Code\\site - 副本\\admin\\.env	\N	1556daefb8514187	/admin/auth/login	POST	127.0.0.1	\N	2026-11-06 17:27:18.668431	0	\N	0	0	0	2026-11-07 01:27:18.671299	\N
19	d5b27f48-ee2f-49d9-940f-758c247fd10c	INFO	framework.core.config	config	_load_config	137	配置加载完成，共 175 个配置项	\N	1556daefb8514187	/admin/auth/login	POST	127.0.0.1	\N	2026-11-06 17:27:18.668431	0	\N	0	0	0	2026-11-07 01:27:18.671299	\N
20	a065f470-a4c7-4569-b39d-81023942c3e8	ERROR	framework.core.controller	controller	error	96	Error c6d3c7ed-fb14-47c9-8be3-05b2345834f4: 400 - name不能为空	\N	c8e38070105344f1	/admin/demo/create-demo	POST	127.0.0.1	1	2026-11-06 17:27:37.919648	0	\N	0	0	0	2026-11-07 01:27:37.921274	\N
21	81ed1772-cf60-4fdf-b568-c2d986b8b59f	ERROR	admin.demo.demo_controller	demo_controller	destroy_demo	85	物理删除demo失败: Expecting value: line 1 column 7 (char 6)	\N	199e94b019714cf6	/admin/demo/destroy-demo	POST	127.0.0.1	1	2026-11-06 17:27:37.930012	0	\N	0	0	0	2026-11-07 01:27:37.936704	\N
22	6bda23ab-0086-493f-b54d-9ea74451d3be	ERROR	framework.core.controller	controller	error	96	Error aeb3ad02-d381-41c2-bbea-02fe7d563774: 400 - Expecting value: line 1 column 7 (char 6)	Traceback (most recent call last):\n  File "C:\\1.Code\\site - 副本\\admin\\demo\\demo_controller.py", line 78, in destroy_demo\n    data = (await self.request.json()).get("data", {})\n            ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\Users\\think\\AppData\\Roaming\\Python\\Python312\\site-packages\\starlette\\requests.py", line 265, in json\n    self._json = json.loads(body)\n                 ^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\__init__.py", line 346, in loads\n    return _default_decoder.decode(s)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\decoder.py", line 338, in decode\n    obj, end = self.raw_decode(s, idx=_w(s, 0).end())\n               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\decoder.py", line 356, in raw_decode\n    raise JSONDecodeError("Expecting value", s, err.value) from None\njson.decoder.JSONDecodeError: Expecting value: line 1 column 7 (char 6)	199e94b019714cf6	/admin/demo/destroy-demo	POST	127.0.0.1	1	2026-11-06 17:27:37.935514	0	\N	0	0	0	2026-11-07 01:27:37.936704	\N
23	861ec56a-de7e-4d15-9e71-7061b4ece79f	ERROR	framework.core.controller	controller	error	96	Error 55ad5281-edbe-4f14-a2c5-dba55cd1c290: 400 - name不能为空	\N	7738ddd6b21f480c	/admin/demo/create-demo	POST	127.0.0.1	1	2026-11-06 17:28:14.061125	0	\N	0	0	0	2026-11-07 01:28:14.062651	\N
24	f22aeb57-74a2-4bc9-9e5d-e31aaecddbf7	ERROR	admin.demo.demo_controller	demo_controller	destroy_demo	85	物理删除demo失败: Expecting value: line 1 column 7 (char 6)	\N	e044f350ee09422a	/admin/demo/destroy-demo	POST	127.0.0.1	1	2026-11-06 17:28:14.133956	0	\N	0	0	0	2026-11-07 01:28:14.136073	\N
25	50276f72-b041-47a4-a012-43ffb4c15327	ERROR	framework.core.controller	controller	error	96	Error e4da94d5-21ac-4c5c-b858-97755897ddd6: 400 - Expecting value: line 1 column 7 (char 6)	Traceback (most recent call last):\n  File "C:\\1.Code\\site - 副本\\admin\\demo\\demo_controller.py", line 78, in destroy_demo\n    data = (await self.request.json()).get("data", {})\n            ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\Users\\think\\AppData\\Roaming\\Python\\Python312\\site-packages\\starlette\\requests.py", line 265, in json\n    self._json = json.loads(body)\n                 ^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\__init__.py", line 346, in loads\n    return _default_decoder.decode(s)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\decoder.py", line 338, in decode\n    obj, end = self.raw_decode(s, idx=_w(s, 0).end())\n               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\ProgramData\\miniconda3\\Lib\\json\\decoder.py", line 356, in raw_decode\n    raise JSONDecodeError("Expecting value", s, err.value) from None\njson.decoder.JSONDecodeError: Expecting value: line 1 column 7 (char 6)	e044f350ee09422a	/admin/demo/destroy-demo	POST	127.0.0.1	1	2026-11-06 17:28:14.135467	0	\N	0	0	0	2026-11-07 01:28:14.136073	\N
\.


--
-- Data for Name: x_menu; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_menu (id, data_id, title, name, pid, path, component, icon, sort, type, permission, status, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
25	5573dcd3-1032-42fa-abfd-e87edf2e5c70	系统管理	系统管理	\N	/system		Tools	110	1	nav:system	1	1	1	2026-07-16 10:48:20.116248	2026-09-23 12:53:30.827282	0	\N	0	\N
28	ba95c7b8-9b1c-4a5c-9883-c134447c3a1d	组织管理	组织管理	25	/organization		UserFilled	20	2	nav:organization	1	1	1	2026-07-16 10:48:26.259616	2026-09-23 12:53:30.827282	0	\N	0	\N
59	725fcda4-e01d-4797-a6c2-62c8c770e923	权限组管理	权限组管理	25	/permission-group		Lock	30	2	nav:permission-group	1	1	1	2026-09-19 09:32:19.711052	2026-09-23 12:53:30.827282	0	\N	0	\N
29	793bcac0-f1ad-4a55-91ce-12d3849d9ac6	菜单管理	菜单管理	25	/menu		Menu	40	2	nav:menu	1	1	1	2026-07-16 10:48:28.3275	2026-09-23 12:53:30.827282	0	\N	0	\N
46	f6a02688-81e1-4b6a-8ac3-9f1f0511653f	日志管理	日志管理	25	/log		Document	50	2	nav:log	1	1	1	2026-09-15 19:40:35.143034	2026-09-23 12:53:30.827282	0	\N	0	\N
30	5a469030-44a3-4e76-8a29-5d2112585e44	个人设置	个人设置	25	/profile		Setting	60	2		1	1	1	2026-07-16 10:48:30.364077	2026-09-23 12:53:30.827282	0	\N	0	\N
24	83159bd4-c2d0-4fb9-8508-f35d7d9d3e37	仪表盘	仪表盘	\N	/dashboard		Odometer	10	2	nav:dashboard	1	1	1	2026-07-16 10:48:18.044957	2026-09-23 12:53:30.827282	0	\N	0	\N
73	6586dfd1-7c66-41dc-9622-4b791e34d42a	Demo 示例	Demo	\N	/demo	demo/Demo	Star	5	2	nav:demo	1	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
\.


--
-- Data for Name: x_notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_notification (id, title, content, type, subtype, download_url, read, "timestamp", created_at, updated_at, data_id, status, create_time, create_by, update_time, update_by, delete_time, delete_by, is_deleted, remark) FROM stdin;
\.


--
-- Data for Name: x_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission (id, data_id, pid, title, code, module, type, path, icon, sort, status, description, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
1	ff815bff-f053-45fd-98be-a92768707e67	0	导航菜单	g:nav	nav	0	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.768433	2026-11-05 15:38:26.768433	0	\N	0	\N
2	5f841a8c-cfb7-48af-8776-e9b7c6ea1a24	1	仪表盘	nav:dashboard	dashboard	1	/dashboard	Odometer	1	1	\N	0	0	2026-11-05 15:38:26.770546	2026-11-05 15:38:26.770546	0	\N	0	\N
8	46d55b51-7673-414e-96d2-df535754c14f	1	附件管理	nav:attachment	attachment	1	/attachment	\N	9	1	\N	0	0	2026-11-05 15:38:26.776667	2026-11-05 15:38:26.776667	0	\N	0	\N
9	6846a54b-15ca-4521-977c-dd4b41b87b18	1	系统管理	nav:system	system	1	/system	Setting	11	1	\N	0	0	2026-11-05 15:38:26.777385	2026-11-05 15:38:26.777385	0	\N	0	\N
10	e767c729-6cdd-4af9-b9e3-be40440b967a	1	组织管理	nav:organization	organization	1	/organization	\N	13	1	\N	0	0	2026-11-05 15:38:26.777995	2026-11-05 15:38:26.777995	0	\N	0	\N
11	bb2a1174-6c77-4d3d-80db-52ef63841906	1	权限组管理	nav:permission-group	permission_group	1	/permission-group	\N	14	1	\N	0	0	2026-11-05 15:38:26.778595	2026-11-05 15:38:26.778595	0	\N	0	\N
12	d27dffb8-94b4-445e-8537-006bced14bec	1	菜单管理	nav:menu	sysmenu	1	/menu	\N	15	1	\N	0	0	2026-11-05 15:38:26.779329	2026-11-05 15:38:26.779329	0	\N	0	\N
13	e286789a-d5ac-4026-a9c4-3e885eaeabe3	1	个人设置	nav:profile	profile	1	/profile	\N	16	1	\N	0	0	2026-11-05 15:38:26.780072	2026-11-05 15:38:26.780072	0	\N	0	\N
14	d46c7f72-49a8-4703-bd29-ab829a33097d	1	日志管理	nav:log	log	1	/log	\N	17	1	\N	0	0	2026-11-05 15:38:26.780744	2026-11-05 15:38:26.780744	0	\N	0	\N
22	94c5fe63-8623-4df9-936c-c19c726a10d9	0	菜单管理	g:sysmenu	sysmenu	0	\N	\N	2	1	\N	0	0	2026-11-05 15:38:26.787536	2026-11-05 15:38:26.787536	0	\N	0	\N
23	9673f313-4d9d-4d15-9208-44986065c174	22	菜单查询	sysmenu:list	sysmenu	2	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.788212	2026-11-05 15:38:26.788212	0	\N	0	\N
24	2a2b68d3-33d6-4bce-a7ae-6a7f5d39c70f	22	菜单新增	sysmenu:create	sysmenu	2	\N	\N	2	1	\N	0	0	2026-11-05 15:38:26.788864	2026-11-05 15:38:26.788864	0	\N	0	\N
25	4bbd3819-94c6-451f-8059-afd09b99ac3b	22	菜单修改	sysmenu:update	sysmenu	2	\N	\N	3	1	\N	0	0	2026-11-05 15:38:26.789537	2026-11-05 15:38:26.789537	0	\N	0	\N
26	0d74e93e-5ad9-46cb-ae3c-93c332d6198e	22	菜单删除	sysmenu:delete	sysmenu	2	\N	\N	4	1	\N	0	0	2026-11-05 15:38:26.790338	2026-11-05 15:38:26.790338	0	\N	0	\N
27	25cf7dc3-0711-4a83-b690-634f4e8e05cd	22	菜单导出	sysmenu:export	sysmenu	2	\N	\N	5	1	\N	0	0	2026-11-05 15:38:26.790941	2026-11-05 15:38:26.790941	0	\N	0	\N
28	8b81f09f-fb1c-4dc0-af35-2a86c8d3c768	22	菜单导入	sysmenu:import	sysmenu	2	\N	\N	6	1	\N	0	0	2026-11-05 15:38:26.791834	2026-11-05 15:38:26.791834	0	\N	0	\N
29	32bceed7-44d3-4ed7-b8ef-751529b46edd	0	组织管理	g:org	organization	0	\N	\N	3	1	\N	0	0	2026-11-05 15:38:26.792632	2026-11-05 15:38:26.792632	0	\N	0	\N
30	f5d2c8d6-2fc0-4482-b72f-2c30aeeeed17	29	部门查询	org:dept:list	organization	2	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.79365	2026-11-05 15:38:26.79365	0	\N	0	\N
31	88a035ec-2614-4ab8-8a05-2942a74d18e8	29	部门新增	org:dept:create	organization	2	\N	\N	2	1	\N	0	0	2026-11-05 15:38:26.794262	2026-11-05 15:38:26.794262	0	\N	0	\N
32	5e65f5c6-6caa-4362-aa56-138398c80d6e	29	部门修改	org:dept:update	organization	2	\N	\N	3	1	\N	0	0	2026-11-05 15:38:26.794897	2026-11-05 15:38:26.794897	0	\N	0	\N
33	9f353036-bcdf-4341-b316-a268cd5ad9de	29	部门删除	org:dept:delete	organization	2	\N	\N	4	1	\N	0	0	2026-11-05 15:38:26.795459	2026-11-05 15:38:26.795459	0	\N	0	\N
34	89ca8bfd-0306-478d-b95f-97a1ce2f05fa	29	员工查询	org:user:list	organization	2	\N	\N	5	1	\N	0	0	2026-11-05 15:38:26.79603	2026-11-05 15:38:26.79603	0	\N	0	\N
35	0c0216c4-2eac-44dd-82e7-7e692575531d	29	员工新增	org:user:create	organization	2	\N	\N	6	1	\N	0	0	2026-11-05 15:38:26.796597	2026-11-05 15:38:26.796597	0	\N	0	\N
36	fcc78018-f8f2-48ba-ba7c-af47d4d0c713	29	员工修改	org:user:update	organization	2	\N	\N	7	1	\N	0	0	2026-11-05 15:38:26.797286	2026-11-05 15:38:26.797286	0	\N	0	\N
37	d675420b-eb55-4e6c-950b-bbb0c16071f9	29	员工删除	org:user:delete	organization	2	\N	\N	8	1	\N	0	0	2026-11-05 15:38:26.79815	2026-11-05 15:38:26.79815	0	\N	0	\N
38	e9e45d31-6e62-438b-bce3-42eb75c31df7	29	员工导入	org:user:import	organization	2	\N	\N	9	1	\N	0	0	2026-11-05 15:38:26.79884	2026-11-05 15:38:26.79884	0	\N	0	\N
39	6627ec61-3e92-4a09-9d5e-78803902b850	29	员工导出	org:user:export	organization	2	\N	\N	10	1	\N	0	0	2026-11-05 15:38:26.799753	2026-11-05 15:38:26.799753	0	\N	0	\N
40	9c57c92c-37f3-4e6a-bc5a-b46524dad7a5	29	角色查询	org:role:list	organization	2	\N	\N	11	1	\N	0	0	2026-11-05 15:38:26.80067	2026-11-05 15:38:26.80067	0	\N	0	\N
41	8d729a6f-5ba1-428b-85a4-aeb735887d31	29	角色新增	org:role:create	organization	2	\N	\N	12	1	\N	0	0	2026-11-05 15:38:26.801526	2026-11-05 15:38:26.801526	0	\N	0	\N
42	ea64881e-4807-43a1-888c-61c543c790ba	29	角色修改	org:role:update	organization	2	\N	\N	13	1	\N	0	0	2026-11-05 15:38:26.802242	2026-11-05 15:38:26.802242	0	\N	0	\N
43	7677031a-86cf-442c-a6bf-f623a1fdf989	29	角色删除	org:role:delete	organization	2	\N	\N	14	1	\N	0	0	2026-11-05 15:38:26.803048	2026-11-05 15:38:26.803048	0	\N	0	\N
44	b8407f0e-2acb-4c6e-ae46-115db8d84e03	29	角色导入	org:role:import	organization	2	\N	\N	15	1	\N	0	0	2026-11-05 15:38:26.803973	2026-11-05 15:38:26.803973	0	\N	0	\N
45	a6a90d8c-0c15-444d-99d1-49ed823af954	29	角色导出	org:role:export	organization	2	\N	\N	16	1	\N	0	0	2026-11-05 15:38:26.804854	2026-11-05 15:38:26.804854	0	\N	0	\N
46	704a1268-1d0f-452f-850f-18387a4d10ad	29	角色授权（成员/权限）	org:role:grant	organization	2	\N	\N	17	1	\N	0	0	2026-11-05 15:38:26.80579	2026-11-05 15:38:26.80579	0	\N	0	\N
71	6a61c670-4ecc-4f3e-8742-f32fef1e2737	0	附件管理	g:attachment	attachment	0	\N	\N	7	1	\N	0	0	2026-11-05 15:38:26.827199	2026-11-05 15:38:26.827199	0	\N	0	\N
72	9fbdc553-c9a4-450a-8428-becc63c6dc9d	71	附件查询	attachment:list	attachment	2	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.827948	2026-11-05 15:38:26.827948	0	\N	0	\N
73	3b63e9db-d9c5-4d53-87ce-33fa966d16c2	71	附件新增	attachment:create	attachment	2	\N	\N	2	1	\N	0	0	2026-11-05 15:38:26.828554	2026-11-05 15:38:26.828554	0	\N	0	\N
74	cfa90513-371e-47f2-aa01-1be699b076ab	71	附件修改	attachment:update	attachment	2	\N	\N	3	1	\N	0	0	2026-11-05 15:38:26.829209	2026-11-05 15:38:26.829209	0	\N	0	\N
75	4250167b-30d5-4581-ad4e-ffd569b0db3a	71	附件删除	attachment:delete	attachment	2	\N	\N	4	1	\N	0	0	2026-11-05 15:38:26.829926	2026-11-05 15:38:26.829926	0	\N	0	\N
76	40e984d6-6773-4a54-9ce1-4344b60b91a7	71	附件上传	attachment:upload	attachment	2	\N	\N	5	1	\N	0	0	2026-11-05 15:38:26.830795	2026-11-05 15:38:26.830795	0	\N	0	\N
77	80d59241-3b37-401e-9f57-c9b82334159e	71	附件下载预览	attachment:download	attachment	2	\N	\N	6	1	\N	0	0	2026-11-05 15:38:26.831551	2026-11-05 15:38:26.831551	0	\N	0	\N
85	cda39933-7590-4184-8fc7-b83ea5595564	0	系统日志	g:log	log	0	\N	\N	9	1	\N	0	0	2026-11-05 15:38:26.83875	2026-11-05 15:38:26.83875	0	\N	0	\N
86	c8baf6de-c4d6-45ac-976c-a2700ca45985	85	日志查询	log:list	log	2	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.839504	2026-11-05 15:38:26.839504	0	\N	0	\N
87	c0fb510c-0c6c-44a0-a486-bb5822c963db	85	日志写入	log:write	log	2	\N	\N	2	1	\N	0	0	2026-11-05 15:38:26.840222	2026-11-05 15:38:26.840222	0	\N	0	\N
88	619c9eae-6969-4ab0-88bf-938c612c1096	85	日志删除	log:delete	log	2	\N	\N	3	1	\N	0	0	2026-11-05 15:38:26.840816	2026-11-05 15:38:26.840816	0	\N	0	\N
89	0117a405-d66e-465d-af75-c279b8f78f97	85	日志清理	log:clean	log	2	\N	\N	4	1	\N	0	0	2026-11-05 15:38:26.841395	2026-11-05 15:38:26.841395	0	\N	0	\N
90	d9de16fb-70c5-4925-bd6a-5af16ddee522	0	仪表盘	g:dashboard	dashboard	0	\N	\N	10	1	\N	0	0	2026-11-05 15:38:26.841953	2026-11-05 15:38:26.841953	0	\N	0	\N
91	8db6c2e1-d53f-4528-a654-ba6919c67f11	90	仪表盘查看	dashboard:view	dashboard	2	\N	\N	1	1	\N	0	0	2026-11-05 15:38:26.842831	2026-11-05 15:38:26.842831	0	\N	0	\N
125	3050c18a-7812-4cd3-bc8c-6ebde30f628b	0	Demo 示例	g:demo	demo	0	\N	\N	30	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
126	c35c3840-4d4e-4828-ae94-a576f91b5457	1	Demo 示例	nav:demo	demo	1	\N	\N	3	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
127	8d521ced-d4df-4740-81b4-f511bb79aaeb	125	demo 查询	demo:list	demo	2	\N	\N	1	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
128	cd7a1727-56cf-4008-841e-6d9a7c998394	125	demo 新增	demo:create	demo	2	\N	\N	2	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
129	677d9b82-c8ac-4abe-8bfa-45008fe34f8d	125	demo 修改	demo:update	demo	2	\N	\N	3	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
130	0d3c8570-2f41-47cb-900d-c76f501a3c2a	125	demo 删除	demo:delete	demo	2	\N	\N	4	1	\N	0	0	2026-11-07 00:30:45.024571	2026-11-07 00:30:45.024571	0	\N	0	\N
\.


--
-- Data for Name: x_permission_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission_group (id, data_id, code, title, menu_id, module, sort, status, description, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_permission_group_data; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission_group_data (id, data_id, group_id, module, scope, custom_dept_ids, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_permission_group_field; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission_group_field (id, data_id, group_id, module, field, field_label, visible, editable, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_permission_group_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission_group_permission (id, data_id, group_id, permission_id, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_permission_group_subject; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_permission_group_subject (id, data_id, group_id, subject_type, subject_id, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_role; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_role (id, data_id, title, name, code, description, status, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
7	bdf456f7-fc82-4f86-88c6-c8b11e1f76a2	管理员	管理员	admin	系统管理员，拥有系统全部权限	1	0	0	2026-09-15 10:07:45.367361	2026-09-15 10:07:45.367361	0	\N	0	\N
\.


--
-- Data for Name: x_role_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_role_permission (id, data_id, role_id, permission_id, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_user (id, data_id, title, username, password, name, phone, email, dept_id, avatar, status, last_login_time, create_by, update_by, create_time, update_time, is_deleted, token, image_path, attachment_ids, delete_time, delete_by, remark) FROM stdin;
1	54dfb963-4765-4282-a40c-fdc22dcdef48	超级管理员	admin	$2b$12$p8150NzTfKJwXBOaeS9Ej.pYL.gIiITOpLtvAuag9ZZvuV.AdzyFe	测试用户	13800138000	test@example.com	\N	\N	1	2026-11-07 01:28:43.431196	0	0	2026-02-28 10:26:15.831978	2026-02-28 10:26:15.831978	0	token1	\N	\N	\N	0	\N
\.


--
-- Data for Name: x_user_api_key; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_user_api_key (id, user_id, name, key, status, description, create_time, created_at, updated_at, expire_time, data_id, create_by, update_by, delete_by, update_time, delete_time, is_deleted, remark) FROM stdin;
\.


--
-- Data for Name: x_user_login; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_user_login (id, user_id, ip, user_agent, login_time, status, created_at, data_id, create_by, update_by, delete_by, create_time, update_time, delete_time, is_deleted, remark) FROM stdin;
\.


--
-- Data for Name: x_user_permission_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_user_permission_group (id, data_id, user_id, group_id, is_active, activate_time, create_by, update_by, create_time, update_time, is_deleted, delete_time, delete_by, remark) FROM stdin;
\.


--
-- Data for Name: x_user_role; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.x_user_role (id, data_id, user_id, role_id, create_by, create_time, title, status, update_time, update_by, delete_time, delete_by, is_deleted, remark) FROM stdin;
1	c1974e0d-9b72-49cc-9a4b-2dfc238db5ca	1	7	0	2026-02-28 10:26:15.838595	管理员	1	2026-09-15 10:07:45.367361	0	\N	0	0	\N
\.


--
-- Name: form_attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.form_attachments_id_seq', 44, true);


--
-- Name: x_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_attachment_id_seq', 528, true);


--
-- Name: x_demo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_demo_id_seq', 2, true);


--
-- Name: x_dept_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_dept_id_seq', 43, true);


--
-- Name: x_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_log_id_seq', 25, true);


--
-- Name: x_menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_menu_id_seq', 73, true);


--
-- Name: x_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_notification_id_seq', 154, true);


--
-- Name: x_permission_group_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_group_data_id_seq', 139, true);


--
-- Name: x_permission_group_field_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_group_field_id_seq', 526, true);


--
-- Name: x_permission_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_group_id_seq', 1136, true);


--
-- Name: x_permission_group_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_group_permission_id_seq', 527, true);


--
-- Name: x_permission_group_subject_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_group_subject_id_seq', 303, true);


--
-- Name: x_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_permission_id_seq', 130, true);


--
-- Name: x_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_role_id_seq', 5524, true);


--
-- Name: x_role_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_role_permission_id_seq', 1, false);


--
-- Name: x_user_api_key_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_user_api_key_id_seq', 134, true);


--
-- Name: x_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_user_id_seq', 37, true);


--
-- Name: x_user_login_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_user_login_id_seq', 1, false);


--
-- Name: x_user_permission_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_user_permission_group_id_seq', 161, true);


--
-- Name: x_user_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.x_user_role_id_seq', 5526, true);


--
-- Name: form_attachments form_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_attachments
    ADD CONSTRAINT form_attachments_pkey PRIMARY KEY (id);


--
-- Name: x_attachment pk_x_attachment; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_attachment
    ADD CONSTRAINT pk_x_attachment PRIMARY KEY (id);


--
-- Name: x_dept pk_x_dept; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_dept
    ADD CONSTRAINT pk_x_dept PRIMARY KEY (id);


--
-- Name: x_notification pk_x_notification; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_notification
    ADD CONSTRAINT pk_x_notification PRIMARY KEY (id);


--
-- Name: x_role pk_x_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_role
    ADD CONSTRAINT pk_x_role PRIMARY KEY (id);


--
-- Name: x_user pk_x_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user
    ADD CONSTRAINT pk_x_user PRIMARY KEY (id);


--
-- Name: x_user_role pk_x_user_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_role
    ADD CONSTRAINT pk_x_user_role PRIMARY KEY (id);


--
-- Name: x_demo x_demo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_demo
    ADD CONSTRAINT x_demo_pkey PRIMARY KEY (id);


--
-- Name: x_dept x_dept_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_dept
    ADD CONSTRAINT x_dept_code_key UNIQUE (code);


--
-- Name: x_log x_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_log
    ADD CONSTRAINT x_log_pkey PRIMARY KEY (id);


--
-- Name: x_menu x_menu_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_menu
    ADD CONSTRAINT x_menu_pkey PRIMARY KEY (id);


--
-- Name: x_permission_group_data x_permission_group_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission_group_data
    ADD CONSTRAINT x_permission_group_data_pkey PRIMARY KEY (id);


--
-- Name: x_permission_group_field x_permission_group_field_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission_group_field
    ADD CONSTRAINT x_permission_group_field_pkey PRIMARY KEY (id);


--
-- Name: x_permission_group_permission x_permission_group_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission_group_permission
    ADD CONSTRAINT x_permission_group_permission_pkey PRIMARY KEY (id);


--
-- Name: x_permission_group x_permission_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission_group
    ADD CONSTRAINT x_permission_group_pkey PRIMARY KEY (id);


--
-- Name: x_permission_group_subject x_permission_group_subject_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission_group_subject
    ADD CONSTRAINT x_permission_group_subject_pkey PRIMARY KEY (id);


--
-- Name: x_permission x_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_permission
    ADD CONSTRAINT x_permission_pkey PRIMARY KEY (id);


--
-- Name: x_role x_role_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_role
    ADD CONSTRAINT x_role_code_key UNIQUE (code);


--
-- Name: x_role x_role_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_role
    ADD CONSTRAINT x_role_name_key UNIQUE (name);


--
-- Name: x_role_permission x_role_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_role_permission
    ADD CONSTRAINT x_role_permission_pkey PRIMARY KEY (id);


--
-- Name: x_user_api_key x_user_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_api_key
    ADD CONSTRAINT x_user_api_key_pkey PRIMARY KEY (id);


--
-- Name: x_user x_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user
    ADD CONSTRAINT x_user_email_key UNIQUE (email);


--
-- Name: x_user_login x_user_login_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_login
    ADD CONSTRAINT x_user_login_pkey PRIMARY KEY (id);


--
-- Name: x_user_permission_group x_user_permission_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user_permission_group
    ADD CONSTRAINT x_user_permission_group_pkey PRIMARY KEY (id);


--
-- Name: x_user x_user_phone_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user
    ADD CONSTRAINT x_user_phone_key UNIQUE (phone);


--
-- Name: x_user x_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.x_user
    ADD CONSTRAINT x_user_username_key UNIQUE (username);


--
-- Name: idx_attachment_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attachment_data_id ON public.x_attachment USING btree (data_id);


--
-- Name: idx_attachment_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attachment_module ON public.x_attachment USING btree (module);


--
-- Name: idx_attachment_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attachment_status ON public.x_attachment USING btree (status);


--
-- Name: idx_attachment_upload_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attachment_upload_time ON public.x_attachment USING btree (upload_time);


--
-- Name: idx_attachment_upload_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attachment_upload_user_id ON public.x_attachment USING btree (upload_user_id);


--
-- Name: idx_form_attachments_form_code_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_form_attachments_form_code_create_time ON public.form_attachments USING btree (form_code, create_time DESC);


--
-- Name: idx_form_attachments_lead_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_form_attachments_lead_id ON public.form_attachments USING btree (lead_id);


--
-- Name: idx_form_attachments_upload_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_form_attachments_upload_status ON public.form_attachments USING btree (upload_status) WHERE (((upload_status)::text <> 'uploaded'::text) AND (is_deleted = 0));


--
-- Name: idx_permission_group_menu; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_group_menu ON public.x_permission_group USING btree (menu_id);


--
-- Name: idx_permission_group_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_group_module ON public.x_permission_group USING btree (module);


--
-- Name: idx_permission_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_module ON public.x_permission USING btree (module);


--
-- Name: idx_permission_pid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permission_pid ON public.x_permission USING btree (pid);


--
-- Name: idx_pg_data_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pg_data_group ON public.x_permission_group_data USING btree (group_id);


--
-- Name: idx_pg_field_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pg_field_group ON public.x_permission_group_field USING btree (group_id);


--
-- Name: idx_pg_permission_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pg_permission_group ON public.x_permission_group_permission USING btree (group_id);


--
-- Name: idx_pg_subject_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pg_subject_target ON public.x_permission_group_subject USING btree (subject_type, subject_id);


--
-- Name: idx_role_permission_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permission_role ON public.x_role_permission USING btree (role_id);


--
-- Name: idx_x_demo_is_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_demo_is_deleted ON public.x_demo USING btree (is_deleted);


--
-- Name: idx_x_demo_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_demo_status ON public.x_demo USING btree (status);


--
-- Name: idx_x_dept_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_dept_data_id ON public.x_dept USING btree (data_id);


--
-- Name: idx_x_dept_pid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_dept_pid ON public.x_dept USING btree (pid);


--
-- Name: idx_x_log_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_log_create_time ON public.x_log USING btree (create_time);


--
-- Name: idx_x_log_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_log_level ON public.x_log USING btree (level);


--
-- Name: idx_x_log_logger; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_log_logger ON public.x_log USING btree (logger);


--
-- Name: idx_x_log_request_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_log_request_id ON public.x_log USING btree (request_id);


--
-- Name: idx_x_menu_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_menu_data_id ON public.x_menu USING btree (data_id);


--
-- Name: idx_x_menu_pid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_menu_pid ON public.x_menu USING btree (pid);


--
-- Name: idx_x_notification_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_notification_read ON public.x_notification USING btree (read);


--
-- Name: idx_x_notification_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_notification_timestamp ON public.x_notification USING btree ("timestamp");


--
-- Name: idx_x_notification_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_notification_type ON public.x_notification USING btree (type);


--
-- Name: idx_x_role_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_role_data_id ON public.x_role USING btree (data_id);


--
-- Name: idx_x_user_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_data_id ON public.x_user USING btree (data_id);


--
-- Name: idx_x_user_dept_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_dept_id ON public.x_user USING btree (dept_id);


--
-- Name: idx_x_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_email ON public.x_user USING btree (email);


--
-- Name: idx_x_user_image_path; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_image_path ON public.x_user USING btree (image_path);


--
-- Name: idx_x_user_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_phone ON public.x_user USING btree (phone);


--
-- Name: idx_x_user_role_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_role_data_id ON public.x_user_role USING btree (data_id);


--
-- Name: idx_x_user_role_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_role_role_id ON public.x_user_role USING btree (role_id);


--
-- Name: idx_x_user_role_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_role_user_id ON public.x_user_role USING btree (user_id);


--
-- Name: idx_x_user_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_x_user_username ON public.x_user USING btree (username);


--
-- Name: uk_form_attachments_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_form_attachments_uuid ON public.form_attachments USING btree (uuid);


--
-- Name: ux_permission_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_permission_code ON public.x_permission USING btree (code) WHERE (is_deleted = 0);


--
-- Name: ux_permission_group_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_permission_group_code ON public.x_permission_group USING btree (code) WHERE (is_deleted = 0);


--
-- Name: ux_pg_data; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_pg_data ON public.x_permission_group_data USING btree (group_id, module) WHERE (is_deleted = 0);


--
-- Name: ux_pg_field; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_pg_field ON public.x_permission_group_field USING btree (group_id, module, field) WHERE (is_deleted = 0);


--
-- Name: ux_pg_permission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_pg_permission ON public.x_permission_group_permission USING btree (group_id, permission_id) WHERE (is_deleted = 0);


--
-- Name: ux_pg_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_pg_subject ON public.x_permission_group_subject USING btree (group_id, subject_type, subject_id) WHERE (is_deleted = 0);


--
-- Name: ux_role_permission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_role_permission ON public.x_role_permission USING btree (role_id, permission_id) WHERE (is_deleted = 0);


--
-- Name: ux_user_pg; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_user_pg ON public.x_user_permission_group USING btree (user_id, group_id) WHERE (is_deleted = 0);


--
-- Name: ux_user_pg_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_user_pg_active ON public.x_user_permission_group USING btree (user_id) WHERE ((is_active = 1) AND (is_deleted = 0));


--
-- Name: form_attachments trigger_form_attachments_update_time; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_form_attachments_update_time BEFORE UPDATE ON public.form_attachments FOR EACH ROW EXECUTE FUNCTION public.update_update_time();


--
-- Name: x_attachment update_x_attachment_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_x_attachment_timestamp BEFORE UPDATE ON public.x_attachment FOR EACH ROW EXECUTE FUNCTION public.update_timestamp_column();


--
-- PostgreSQL database dump complete
--

\unrestrict fdwYrIvchWikEY9wR6Dg5H6c3n9g7Qoo6rY4d5pIA56KKUlypEzptD6nOW4WbPx

