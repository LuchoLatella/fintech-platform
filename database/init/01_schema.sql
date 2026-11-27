--
-- PostgreSQL database dump
--

\restrict fs3uXScWfd7aIBYH4gbZLMp6EOX5cPeNteDZgw6jOorcbiDOIRmXoHuri2Y47vi

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: btree_gin; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA public;


--
-- Name: EXTENSION btree_gin; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION btree_gin IS 'support for indexing common datatypes in GIN';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: get_portfolio_position(uuid, uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_portfolio_position(p_portfolio_id uuid, p_asset_id uuid) RETURNS TABLE(quantity numeric, avg_cost numeric, cost_basis numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        pp.quantity,
        pp.avg_cost,
        pp.quantity * pp.avg_cost AS cost_basis
    FROM portfolio_positions pp
    WHERE pp.portfolio_id = p_portfolio_id
      AND pp.asset_id = p_asset_id
      AND pp.is_open = TRUE;
END;
$$;


--
-- Name: refresh_arg_indicators(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_arg_indicators() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY arg_latest_indicators;
END;
$$;


--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _compressed_hypertable_4; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._compressed_hypertable_4 (
);


--
-- Name: price_ticks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.price_ticks (
    "time" timestamp with time zone NOT NULL,
    asset_id uuid NOT NULL,
    price numeric(20,6) NOT NULL,
    bid numeric(20,6),
    ask numeric(20,6),
    volume numeric(20,2),
    source character varying(30)
);


--
-- Name: _hyper_2_1_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_2_1_chunk (
    CONSTRAINT constraint_1 CHECK ((("time" >= '2026-11-27 00:00:00+00'::timestamp with time zone) AND ("time" < '2026-11-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.price_ticks);


--
-- Name: ai_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_models (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    version character varying(20) NOT NULL,
    model_type character varying(50),
    asset_class character varying(30),
    timeframe character varying(5),
    is_active boolean NOT NULL,
    accuracy numeric(6,4),
    sharpe_backtest numeric(8,4),
    trained_at timestamp with time zone,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: ai_models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_models_id_seq OWNED BY public.ai_models.id;


--
-- Name: ai_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_signals (
    id uuid NOT NULL,
    asset_id uuid NOT NULL,
    symbol character varying(30),
    exchange character varying(20),
    timeframe character varying(5),
    scanner_source character varying(30),
    scanner_rank integer,
    signal_type character varying(20) NOT NULL,
    strategy character varying(30),
    trend character varying(20),
    market_regime character varying(20),
    confidence numeric(5,2) NOT NULL,
    ml_probability_bull numeric(5,2),
    ml_probability_bear numeric(5,2),
    risk_score numeric(5,2),
    reward_score numeric(5,2),
    expected_return numeric(8,4),
    risk_reward numeric(8,4),
    entry_price numeric(20,6),
    stop_loss numeric(20,6),
    take_profit_1 numeric(20,6),
    take_profit_2 numeric(20,6),
    rationale text,
    technical_factors jsonb,
    fundamental_factors jsonb,
    sentiment_score numeric(5,2),
    is_active boolean NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone,
    invalidated_at timestamp with time zone,
    invalidation_reason text,
    is_executed boolean NOT NULL,
    execution_price numeric(20,6),
    pnl_percent numeric(10,4),
    backtest_id character varying(50),
    model_id integer
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: alert_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_events (
    id uuid NOT NULL,
    rule_id uuid NOT NULL,
    asset_id uuid,
    triggered_value numeric(20,6),
    message text NOT NULL,
    channels_sent text[],
    was_delivered boolean NOT NULL,
    delivery_errors jsonb,
    triggered_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alert_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_rules (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    asset_id uuid,
    alert_name character varying(100) NOT NULL,
    alert_type character varying(30) NOT NULL,
    condition_value numeric(20,6),
    condition_pct numeric(8,4),
    timeframe character varying(5),
    channels text[],
    is_active boolean NOT NULL,
    repeat boolean NOT NULL,
    cooldown_minutes integer NOT NULL,
    last_triggered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: api_rate_limits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_rate_limits (
    key_value character varying(255) NOT NULL,
    endpoint character varying(255) NOT NULL,
    window_start timestamp with time zone NOT NULL,
    request_count integer DEFAULT 1
);


--
-- Name: arg_debt_auctions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.arg_debt_auctions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    auction_date date NOT NULL,
    instrument character varying(100) NOT NULL,
    isin character varying(20),
    cut_rate numeric(10,4),
    amount_offered numeric(24,2),
    amount_awarded numeric(24,2),
    currency character varying(5),
    maturity_date date,
    source character varying(30),
    raw_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: arg_economic_indicators; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.arg_economic_indicators (
    id integer NOT NULL,
    indicator_code character varying(50) NOT NULL,
    indicator_name character varying(100) NOT NULL,
    value numeric(20,6) NOT NULL,
    unit character varying(20),
    period date,
    source character varying(50),
    metadata jsonb,
    recorded_at timestamp with time zone DEFAULT now()
);


--
-- Name: arg_economic_indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.arg_economic_indicators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: arg_economic_indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.arg_economic_indicators_id_seq OWNED BY public.arg_economic_indicators.id;


--
-- Name: arg_latest_indicators; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.arg_latest_indicators AS
 SELECT DISTINCT ON (arg_economic_indicators.indicator_code) arg_economic_indicators.indicator_code,
    arg_economic_indicators.indicator_name,
    arg_economic_indicators.value,
    arg_economic_indicators.unit,
    arg_economic_indicators.period,
    arg_economic_indicators.source,
    arg_economic_indicators.recorded_at
   FROM public.arg_economic_indicators
  ORDER BY arg_economic_indicators.indicator_code, arg_economic_indicators.recorded_at DESC
  WITH NO DATA;


--
-- Name: asset_classes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.asset_classes (
    id integer NOT NULL,
    code character varying(30) NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: asset_classes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.asset_classes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: asset_classes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.asset_classes_id_seq OWNED BY public.asset_classes.id;


--
-- Name: assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assets (
    id uuid NOT NULL,
    symbol character varying(30) NOT NULL,
    exchange_id integer,
    asset_class_id integer,
    name character varying(255) NOT NULL,
    description text,
    currency character varying(5) NOT NULL,
    isin character varying(20),
    sector character varying(100),
    industry character varying(100),
    country character varying(5),
    is_active boolean NOT NULL,
    is_argentine boolean NOT NULL,
    underlying_symbol character varying(30),
    ratio numeric(10,4),
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id bigint NOT NULL,
    user_id uuid,
    action character varying(100) NOT NULL,
    entity_type character varying(50),
    entity_id text,
    ip_address inet,
    user_agent text,
    request_data jsonb,
    response_code smallint,
    duration_ms integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: backtest_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backtest_runs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(150),
    strategy_type character varying(50),
    asset_ids uuid[],
    timeframe character varying(5),
    start_date date NOT NULL,
    end_date date NOT NULL,
    initial_capital numeric(20,4) NOT NULL,
    parameters jsonb NOT NULL,
    final_capital numeric(20,4),
    total_return numeric(10,4),
    annualized_return numeric(10,4),
    max_drawdown numeric(10,4),
    sharpe_ratio numeric(8,4),
    sortino_ratio numeric(8,4),
    calmar_ratio numeric(8,4),
    win_rate numeric(8,4),
    total_trades integer,
    winning_trades integer,
    losing_trades integer,
    avg_win numeric(10,4),
    avg_loss numeric(10,4),
    profit_factor numeric(8,4),
    status character varying(15) DEFAULT 'pending'::character varying,
    error_message text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT backtest_runs_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: backtest_trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backtest_trades (
    id bigint NOT NULL,
    run_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    side character varying(5),
    quantity numeric(20,8),
    entry_price numeric(20,6),
    exit_price numeric(20,6),
    entry_time timestamp with time zone,
    exit_time timestamp with time zone,
    pnl numeric(20,6),
    pnl_pct numeric(10,4),
    exit_reason character varying(30),
    CONSTRAINT backtest_trades_side_check CHECK (((side)::text = ANY ((ARRAY['buy'::character varying, 'sell'::character varying])::text[])))
);


--
-- Name: backtest_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.backtest_trades_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: backtest_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.backtest_trades_id_seq OWNED BY public.backtest_trades.id;


--
-- Name: exchange_rates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exchange_rates (
    "time" timestamp with time zone NOT NULL,
    from_currency character varying(5) NOT NULL,
    to_currency character varying(5) NOT NULL,
    rate numeric(20,6) NOT NULL,
    rate_type character varying(20) NOT NULL,
    source character varying(30)
);


--
-- Name: exchanges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exchanges (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    country character varying(5),
    currency character varying(5),
    timezone character varying(50)
);


--
-- Name: exchanges_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.exchanges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: exchanges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.exchanges_id_seq OWNED BY public.exchanges.id;


--
-- Name: fundamental_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fundamental_data (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    asset_id uuid NOT NULL,
    period date NOT NULL,
    period_type character varying(10) DEFAULT 'TTM'::character varying,
    market_cap numeric(24,2),
    enterprise_value numeric(24,2),
    pe_ratio numeric(12,4),
    forward_pe numeric(12,4),
    pb_ratio numeric(12,4),
    ps_ratio numeric(12,4),
    ev_ebitda numeric(12,4),
    revenue numeric(24,2),
    gross_profit numeric(24,2),
    ebitda numeric(24,2),
    net_income numeric(24,2),
    eps numeric(12,4),
    roe numeric(10,4),
    roa numeric(10,4),
    roic numeric(10,4),
    current_ratio numeric(10,4),
    quick_ratio numeric(10,4),
    debt_to_equity numeric(10,4),
    net_debt numeric(24,2),
    interest_coverage numeric(10,4),
    revenue_growth_yoy numeric(10,4),
    earnings_growth_yoy numeric(10,4),
    dividend_yield numeric(10,4),
    payout_ratio numeric(10,4),
    dividend_per_share numeric(12,4),
    operating_cf numeric(24,2),
    capex numeric(24,2),
    free_cash_flow numeric(24,2),
    fundamental_score numeric(5,2),
    valuation_score numeric(5,2),
    quality_score numeric(5,2),
    source character varying(30),
    raw_data jsonb,
    fetched_at timestamp with time zone DEFAULT now(),
    CONSTRAINT fundamental_data_period_type_check CHECK (((period_type)::text = ANY ((ARRAY['Q1'::character varying, 'Q2'::character varying, 'Q3'::character varying, 'Q4'::character varying, 'annual'::character varying, 'TTM'::character varying])::text[])))
);


--
-- Name: market_anomalies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.market_anomalies (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    asset_id uuid NOT NULL,
    anomaly_type character varying(50),
    severity character varying(10),
    description text,
    detected_value numeric(20,6),
    expected_range numrange,
    detected_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    CONSTRAINT market_anomalies_severity_check CHECK (((severity)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying])::text[])))
);


--
-- Name: news_articles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.news_articles (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    source character varying(50) NOT NULL,
    headline text NOT NULL,
    summary text,
    url text,
    author character varying(150),
    published_at timestamp with time zone NOT NULL,
    sentiment_score numeric(5,2),
    sentiment_label character varying(15),
    relevance_score numeric(5,2),
    topics text[],
    entities jsonb,
    category character varying(30),
    is_breaking boolean DEFAULT false,
    language character varying(5) DEFAULT 'es'::character varying,
    processed_at timestamp with time zone DEFAULT now(),
    CONSTRAINT news_articles_sentiment_label_check CHECK (((sentiment_label)::text = ANY ((ARRAY['very_negative'::character varying, 'negative'::character varying, 'neutral'::character varying, 'positive'::character varying, 'very_positive'::character varying])::text[])))
);


--
-- Name: news_asset_mentions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.news_asset_mentions (
    news_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    relevance numeric(5,2),
    impact_type character varying(10),
    CONSTRAINT news_asset_mentions_impact_type_check CHECK (((impact_type)::text = ANY ((ARRAY['positive'::character varying, 'negative'::character varying, 'neutral'::character varying])::text[])))
);


--
-- Name: portfolio_positions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolio_positions (
    id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    quantity numeric(24,8) NOT NULL,
    avg_cost numeric(20,6) NOT NULL,
    currency character varying(5) NOT NULL,
    opened_at timestamp with time zone DEFAULT now() NOT NULL,
    closed_at timestamp with time zone,
    is_open boolean NOT NULL,
    notes text
);


--
-- Name: portfolio_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolio_snapshots (
    id integer NOT NULL,
    portfolio_id uuid NOT NULL,
    snapshot_date date NOT NULL,
    total_value_usd numeric(20,4),
    total_value_ars numeric(24,2),
    daily_return numeric(10,6),
    total_return numeric(10,6),
    cash_balance numeric(20,4),
    positions_data jsonb,
    metrics jsonb
);


--
-- Name: portfolio_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.portfolio_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: portfolio_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.portfolio_snapshots_id_seq OWNED BY public.portfolio_snapshots.id;


--
-- Name: portfolio_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolio_transactions (
    id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    transaction_type character varying(10) NOT NULL,
    quantity numeric(24,8) NOT NULL,
    price numeric(20,6) NOT NULL,
    commission numeric(12,4) NOT NULL,
    currency character varying(5) NOT NULL,
    fx_rate numeric(12,6) NOT NULL,
    notes text,
    executed_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: portfolios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolios (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    currency character varying(5) NOT NULL,
    portfolio_type character varying(20) NOT NULL,
    is_default boolean NOT NULL,
    broker character varying(50),
    broker_account character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    cash_balance numeric(20,4) NOT NULL
);


--
-- Name: price_ohlcv; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.price_ohlcv (
    "time" timestamp with time zone NOT NULL,
    asset_id uuid NOT NULL,
    open numeric(20,6) NOT NULL,
    high numeric(20,6) NOT NULL,
    low numeric(20,6) NOT NULL,
    close numeric(20,6) NOT NULL,
    volume numeric(24,2) DEFAULT 0,
    vwap numeric(20,6),
    trades integer,
    source character varying(30),
    timeframe character varying(5) NOT NULL
);


--
-- Name: risk_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_metrics (
    id bigint NOT NULL,
    portfolio_id uuid NOT NULL,
    calculated_at timestamp with time zone NOT NULL,
    var_95_1d numeric(10,4),
    var_99_1d numeric(10,4),
    cvar_95_1d numeric(10,4),
    sharpe_ratio numeric(8,4),
    sortino_ratio numeric(8,4),
    beta numeric(8,4),
    alpha numeric(8,4),
    volatility_ann numeric(10,4),
    max_drawdown numeric(10,4),
    current_drawdown numeric(10,4),
    top1_concentration numeric(8,4),
    top5_concentration numeric(8,4),
    sector_concentration jsonb,
    avg_correlation numeric(8,4),
    diversification_score numeric(5,2)
);


--
-- Name: risk_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.risk_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: risk_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.risk_metrics_id_seq OWNED BY public.risk_metrics.id;


--
-- Name: sentiment_aggregates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sentiment_aggregates (
    id bigint NOT NULL,
    asset_id uuid NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    period_type character varying(5),
    sentiment_avg numeric(5,2),
    sentiment_std numeric(5,2),
    news_count integer DEFAULT 0,
    social_score numeric(5,2),
    fear_greed_idx numeric(5,2),
    CONSTRAINT sentiment_aggregates_period_type_check CHECK (((period_type)::text = ANY ((ARRAY['1h'::character varying, '4h'::character varying, '1d'::character varying, '1w'::character varying])::text[])))
);


--
-- Name: sentiment_aggregates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_aggregates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sentiment_aggregates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sentiment_aggregates_id_seq OWNED BY public.sentiment_aggregates.id;


--
-- Name: support_resistance_levels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.support_resistance_levels (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    asset_id uuid NOT NULL,
    timeframe character varying(5) NOT NULL,
    level_type character varying(10),
    price numeric(20,6) NOT NULL,
    strength numeric(5,2),
    touches integer DEFAULT 1,
    detected_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    CONSTRAINT support_resistance_levels_level_type_check CHECK (((level_type)::text = ANY ((ARRAY['support'::character varying, 'resistance'::character varying])::text[])))
);


--
-- Name: technical_indicators; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.technical_indicators (
    id bigint NOT NULL,
    asset_id uuid NOT NULL,
    timeframe character varying(5) NOT NULL,
    calculated_at timestamp with time zone NOT NULL,
    ema_9 numeric(20,6),
    ema_21 numeric(20,6),
    ema_50 numeric(20,6),
    ema_200 numeric(20,6),
    sma_20 numeric(20,6),
    sma_50 numeric(20,6),
    sma_200 numeric(20,6),
    rsi_14 numeric(8,4),
    macd_line numeric(20,6),
    macd_signal numeric(20,6),
    macd_hist numeric(20,6),
    stoch_k numeric(8,4),
    stoch_d numeric(8,4),
    bb_upper numeric(20,6),
    bb_middle numeric(20,6),
    bb_lower numeric(20,6),
    bb_width numeric(10,6),
    atr_14 numeric(20,6),
    vwap numeric(20,6),
    obv numeric(24,2),
    signals text[],
    trend character varying(10),
    strength numeric(5,2),
    CONSTRAINT technical_indicators_trend_check CHECK (((trend)::text = ANY ((ARRAY['bullish'::character varying, 'bearish'::character varying, 'neutral'::character varying, 'sideways'::character varying])::text[])))
);


--
-- Name: technical_indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.technical_indicators_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: technical_indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.technical_indicators_id_seq OWNED BY public.technical_indicators.id;


--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_preferences (
    user_id uuid NOT NULL,
    default_currency character varying(5) NOT NULL,
    risk_profile character varying(20) NOT NULL,
    preferred_markets text[],
    notification_email boolean NOT NULL,
    notification_telegram boolean NOT NULL,
    telegram_chat_id character varying(100),
    notification_whatsapp boolean NOT NULL,
    whatsapp_number character varying(30),
    theme character varying(10) NOT NULL,
    language character varying(5) NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    refresh_token text NOT NULL,
    device_info jsonb,
    ip_address inet,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password_hash text NOT NULL,
    full_name character varying(255),
    phone character varying(30),
    country character varying(5) NOT NULL,
    plan character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: v_active_signals; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_active_signals AS
 SELECT s.id,
    a.symbol,
    a.name AS asset_name,
    e.code AS exchange,
    ac.code AS asset_class,
    s.signal_type,
    s.strategy,
    s.confidence,
    s.risk_score,
    s.expected_return,
    s.entry_price,
    s.stop_loss,
    s.take_profit_1,
    s.risk_reward,
    s.rationale,
    s.generated_at,
    s.expires_at
   FROM (((public.ai_signals s
     JOIN public.assets a ON ((s.asset_id = a.id)))
     JOIN public.exchanges e ON ((a.exchange_id = e.id)))
     JOIN public.asset_classes ac ON ((a.asset_class_id = ac.id)))
  WHERE ((s.is_active = true) AND ((s.expires_at IS NULL) OR (s.expires_at > now())))
  ORDER BY s.confidence DESC, s.generated_at DESC;


--
-- Name: v_latest_quotes; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_latest_quotes AS
 SELECT DISTINCT ON (price_ohlcv.asset_id, price_ohlcv.timeframe) price_ohlcv.asset_id,
    price_ohlcv.timeframe,
    price_ohlcv."time" AS quote_time,
    price_ohlcv.open,
    price_ohlcv.high,
    price_ohlcv.low,
    price_ohlcv.close,
    price_ohlcv.volume,
    price_ohlcv.vwap
   FROM public.price_ohlcv
  ORDER BY price_ohlcv.asset_id, price_ohlcv.timeframe, price_ohlcv."time" DESC;


--
-- Name: v_portfolio_summary; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_portfolio_summary AS
SELECT
    NULL::uuid AS portfolio_id,
    NULL::uuid AS user_id,
    NULL::character varying(100) AS name,
    NULL::character varying(5) AS currency,
    NULL::bigint AS position_count,
    NULL::numeric AS cost_basis;


--
-- Name: watchlist_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.watchlist_items (
    id uuid NOT NULL,
    watchlist_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    added_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text
);


--
-- Name: watchlists; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.watchlists (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    is_default boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ai_models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_models ALTER COLUMN id SET DEFAULT nextval('public.ai_models_id_seq'::regclass);


--
-- Name: arg_economic_indicators id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.arg_economic_indicators ALTER COLUMN id SET DEFAULT nextval('public.arg_economic_indicators_id_seq'::regclass);


--
-- Name: asset_classes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_classes ALTER COLUMN id SET DEFAULT nextval('public.asset_classes_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: backtest_trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_trades ALTER COLUMN id SET DEFAULT nextval('public.backtest_trades_id_seq'::regclass);


--
-- Name: exchanges id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges ALTER COLUMN id SET DEFAULT nextval('public.exchanges_id_seq'::regclass);


--
-- Name: portfolio_snapshots id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_snapshots ALTER COLUMN id SET DEFAULT nextval('public.portfolio_snapshots_id_seq'::regclass);


--
-- Name: risk_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_metrics ALTER COLUMN id SET DEFAULT nextval('public.risk_metrics_id_seq'::regclass);


--
-- Name: sentiment_aggregates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_aggregates ALTER COLUMN id SET DEFAULT nextval('public.sentiment_aggregates_id_seq'::regclass);


--
-- Name: technical_indicators id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technical_indicators ALTER COLUMN id SET DEFAULT nextval('public.technical_indicators_id_seq'::regclass);


--
-- Name: _hyper_2_1_chunk 1_price_ticks_pkey; Type: CONSTRAINT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk
    ADD CONSTRAINT "1_price_ticks_pkey" PRIMARY KEY ("time", asset_id);


--
-- Name: ai_models ai_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_models
    ADD CONSTRAINT ai_models_pkey PRIMARY KEY (id);


--
-- Name: ai_signals ai_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_signals
    ADD CONSTRAINT ai_signals_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: alert_events alert_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_events
    ADD CONSTRAINT alert_events_pkey PRIMARY KEY (id);


--
-- Name: alert_rules alert_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_pkey PRIMARY KEY (id);


--
-- Name: api_rate_limits api_rate_limits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_rate_limits
    ADD CONSTRAINT api_rate_limits_pkey PRIMARY KEY (key_value, endpoint, window_start);


--
-- Name: arg_debt_auctions arg_debt_auctions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.arg_debt_auctions
    ADD CONSTRAINT arg_debt_auctions_pkey PRIMARY KEY (id);


--
-- Name: arg_economic_indicators arg_economic_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.arg_economic_indicators
    ADD CONSTRAINT arg_economic_indicators_pkey PRIMARY KEY (id);


--
-- Name: asset_classes asset_classes_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_classes
    ADD CONSTRAINT asset_classes_code_key UNIQUE (code);


--
-- Name: asset_classes asset_classes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asset_classes
    ADD CONSTRAINT asset_classes_pkey PRIMARY KEY (id);


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: backtest_runs backtest_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_runs
    ADD CONSTRAINT backtest_runs_pkey PRIMARY KEY (id);


--
-- Name: backtest_trades backtest_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_trades
    ADD CONSTRAINT backtest_trades_pkey PRIMARY KEY (id);


--
-- Name: exchange_rates exchange_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_pkey PRIMARY KEY ("time", from_currency, to_currency, rate_type);


--
-- Name: exchanges exchanges_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_code_key UNIQUE (code);


--
-- Name: exchanges exchanges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_pkey PRIMARY KEY (id);


--
-- Name: fundamental_data fundamental_data_asset_id_period_period_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_asset_id_period_period_type_key UNIQUE (asset_id, period, period_type);


--
-- Name: fundamental_data fundamental_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_pkey PRIMARY KEY (id);


--
-- Name: market_anomalies market_anomalies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.market_anomalies
    ADD CONSTRAINT market_anomalies_pkey PRIMARY KEY (id);


--
-- Name: news_articles news_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_pkey PRIMARY KEY (id);


--
-- Name: news_asset_mentions news_asset_mentions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.news_asset_mentions
    ADD CONSTRAINT news_asset_mentions_pkey PRIMARY KEY (news_id, asset_id);


--
-- Name: portfolio_positions portfolio_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_positions
    ADD CONSTRAINT portfolio_positions_pkey PRIMARY KEY (id);


--
-- Name: portfolio_snapshots portfolio_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_snapshots
    ADD CONSTRAINT portfolio_snapshots_pkey PRIMARY KEY (id);


--
-- Name: portfolio_transactions portfolio_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_transactions
    ADD CONSTRAINT portfolio_transactions_pkey PRIMARY KEY (id);


--
-- Name: portfolios portfolios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_pkey PRIMARY KEY (id);


--
-- Name: price_ohlcv price_ohlcv_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_ohlcv
    ADD CONSTRAINT price_ohlcv_pkey PRIMARY KEY ("time", asset_id, timeframe);


--
-- Name: price_ticks price_ticks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_ticks
    ADD CONSTRAINT price_ticks_pkey PRIMARY KEY ("time", asset_id);


--
-- Name: risk_metrics risk_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_metrics
    ADD CONSTRAINT risk_metrics_pkey PRIMARY KEY (id);


--
-- Name: risk_metrics risk_metrics_portfolio_id_calculated_at_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_metrics
    ADD CONSTRAINT risk_metrics_portfolio_id_calculated_at_key UNIQUE (portfolio_id, calculated_at);


--
-- Name: sentiment_aggregates sentiment_aggregates_asset_id_period_start_period_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_aggregates
    ADD CONSTRAINT sentiment_aggregates_asset_id_period_start_period_type_key UNIQUE (asset_id, period_start, period_type);


--
-- Name: sentiment_aggregates sentiment_aggregates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_aggregates
    ADD CONSTRAINT sentiment_aggregates_pkey PRIMARY KEY (id);


--
-- Name: support_resistance_levels support_resistance_levels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_resistance_levels
    ADD CONSTRAINT support_resistance_levels_pkey PRIMARY KEY (id);


--
-- Name: technical_indicators technical_indicators_asset_id_timeframe_calculated_at_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technical_indicators
    ADD CONSTRAINT technical_indicators_asset_id_timeframe_calculated_at_key UNIQUE (asset_id, timeframe, calculated_at);


--
-- Name: technical_indicators technical_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technical_indicators
    ADD CONSTRAINT technical_indicators_pkey PRIMARY KEY (id);


--
-- Name: assets uq_asset_symbol_exchange; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT uq_asset_symbol_exchange UNIQUE (symbol, exchange_id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (user_id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_refresh_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_refresh_token_key UNIQUE (refresh_token);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: watchlist_items watchlist_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.watchlist_items
    ADD CONSTRAINT watchlist_items_pkey PRIMARY KEY (id);


--
-- Name: watchlists watchlists_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.watchlists
    ADD CONSTRAINT watchlists_pkey PRIMARY KEY (id);


--
-- Name: _hyper_2_1_chunk_price_ticks_time_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_2_1_chunk_price_ticks_time_idx ON _timescaledb_internal._hyper_2_1_chunk USING btree ("time" DESC);


--
-- Name: exchange_rates_time_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX exchange_rates_time_idx ON public.exchange_rates USING btree ("time" DESC);


--
-- Name: idx_alert_events_rule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_events_rule ON public.alert_events USING btree (rule_id, triggered_at DESC);


--
-- Name: idx_arg_indicator_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_arg_indicator_code ON public.arg_economic_indicators USING btree (indicator_code, period DESC);


--
-- Name: idx_arg_latest_indicators_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_arg_latest_indicators_unique ON public.arg_latest_indicators USING btree (indicator_code, period);


--
-- Name: idx_assets_argentine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_argentine ON public.assets USING btree (is_argentine) WHERE (is_argentine = true);


--
-- Name: idx_assets_class; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_class ON public.assets USING btree (asset_class_id);


--
-- Name: idx_assets_exchange; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_exchange ON public.assets USING btree (exchange_id);


--
-- Name: idx_assets_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_symbol ON public.assets USING gin (symbol public.gin_trgm_ops);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_action ON public.audit_log USING btree (action, created_at DESC);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user ON public.audit_log USING btree (user_id, created_at DESC);


--
-- Name: idx_news_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_news_published ON public.news_articles USING btree (published_at DESC);


--
-- Name: idx_news_sentiment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_news_sentiment ON public.news_articles USING btree (sentiment_score, published_at DESC);


--
-- Name: idx_news_topics; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_news_topics ON public.news_articles USING gin (topics);


--
-- Name: idx_price_asset_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_price_asset_time ON public.price_ohlcv USING btree (asset_id, "time" DESC, timeframe);


--
-- Name: idx_signals_asset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_signals_asset ON public.ai_signals USING btree (asset_id, generated_at DESC) WHERE (is_active = true);


--
-- Name: idx_signals_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_signals_type ON public.ai_signals USING btree (signal_type, confidence DESC) WHERE (is_active = true);


--
-- Name: idx_tech_asset_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tech_asset_time ON public.technical_indicators USING btree (asset_id, timeframe, calculated_at DESC);


--
-- Name: ix_ai_signal_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signal_active ON public.ai_signals USING btree (is_active);


--
-- Name: ix_ai_signal_active_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signal_active_confidence ON public.ai_signals USING btree (is_active, confidence);


--
-- Name: ix_ai_signal_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signal_confidence ON public.ai_signals USING btree (confidence);


--
-- Name: ix_ai_signal_scanner_rank; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signal_scanner_rank ON public.ai_signals USING btree (scanner_rank);


--
-- Name: ix_ai_signal_symbol_generated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signal_symbol_generated ON public.ai_signals USING btree (symbol, generated_at);


--
-- Name: ix_ai_signals_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_signals_symbol ON public.ai_signals USING btree (symbol);


--
-- Name: ix_asset_symbol_exchange; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_asset_symbol_exchange ON public.assets USING btree (symbol, exchange_id);


--
-- Name: ix_assets_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_assets_symbol ON public.assets USING btree (symbol);


--
-- Name: price_ohlcv_time_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX price_ohlcv_time_idx ON public.price_ohlcv USING btree ("time" DESC);


--
-- Name: price_ticks_time_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX price_ticks_time_idx ON public.price_ticks USING btree ("time" DESC);


--
-- Name: v_portfolio_summary _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_portfolio_summary AS
 SELECT p.id AS portfolio_id,
    p.user_id,
    p.name,
    p.currency,
    count(pp.id) AS position_count,
    sum((pp.quantity * pp.avg_cost)) AS cost_basis
   FROM (public.portfolios p
     LEFT JOIN public.portfolio_positions pp ON (((p.id = pp.portfolio_id) AND (pp.is_open = true))))
  GROUP BY p.id;


--
-- Name: assets trg_assets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_assets_updated_at BEFORE UPDATE ON public.assets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: portfolios trg_portfolios_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_portfolios_updated_at BEFORE UPDATE ON public.portfolios FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: users trg_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: _hyper_2_1_chunk price_ticks_asset_id_fkey; Type: FK CONSTRAINT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk
    ADD CONSTRAINT price_ticks_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: ai_signals ai_signals_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_signals
    ADD CONSTRAINT ai_signals_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: ai_signals ai_signals_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_signals
    ADD CONSTRAINT ai_signals_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ai_models(id);


--
-- Name: alert_events alert_events_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_events
    ADD CONSTRAINT alert_events_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: alert_events alert_events_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_events
    ADD CONSTRAINT alert_events_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES public.alert_rules(id);


--
-- Name: alert_rules alert_rules_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: alert_rules alert_rules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: assets assets_asset_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_asset_class_id_fkey FOREIGN KEY (asset_class_id) REFERENCES public.asset_classes(id);


--
-- Name: assets assets_exchange_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_exchange_id_fkey FOREIGN KEY (exchange_id) REFERENCES public.exchanges(id);


--
-- Name: audit_log audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: backtest_runs backtest_runs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_runs
    ADD CONSTRAINT backtest_runs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: backtest_trades backtest_trades_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_trades
    ADD CONSTRAINT backtest_trades_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: backtest_trades backtest_trades_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_trades
    ADD CONSTRAINT backtest_trades_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.backtest_runs(id) ON DELETE CASCADE;


--
-- Name: fundamental_data fundamental_data_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamental_data
    ADD CONSTRAINT fundamental_data_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: market_anomalies market_anomalies_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.market_anomalies
    ADD CONSTRAINT market_anomalies_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: news_asset_mentions news_asset_mentions_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.news_asset_mentions
    ADD CONSTRAINT news_asset_mentions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: news_asset_mentions news_asset_mentions_news_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.news_asset_mentions
    ADD CONSTRAINT news_asset_mentions_news_id_fkey FOREIGN KEY (news_id) REFERENCES public.news_articles(id) ON DELETE CASCADE;


--
-- Name: portfolio_positions portfolio_positions_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_positions
    ADD CONSTRAINT portfolio_positions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: portfolio_positions portfolio_positions_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_positions
    ADD CONSTRAINT portfolio_positions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


--
-- Name: portfolio_snapshots portfolio_snapshots_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_snapshots
    ADD CONSTRAINT portfolio_snapshots_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id);


--
-- Name: portfolio_transactions portfolio_transactions_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_transactions
    ADD CONSTRAINT portfolio_transactions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: portfolio_transactions portfolio_transactions_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio_transactions
    ADD CONSTRAINT portfolio_transactions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id);


--
-- Name: portfolios portfolios_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: price_ohlcv price_ohlcv_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_ohlcv
    ADD CONSTRAINT price_ohlcv_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: price_ticks price_ticks_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_ticks
    ADD CONSTRAINT price_ticks_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: risk_metrics risk_metrics_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_metrics
    ADD CONSTRAINT risk_metrics_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id);


--
-- Name: sentiment_aggregates sentiment_aggregates_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_aggregates
    ADD CONSTRAINT sentiment_aggregates_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: support_resistance_levels support_resistance_levels_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.support_resistance_levels
    ADD CONSTRAINT support_resistance_levels_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: technical_indicators technical_indicators_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technical_indicators
    ADD CONSTRAINT technical_indicators_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: user_preferences user_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: watchlist_items watchlist_items_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.watchlist_items
    ADD CONSTRAINT watchlist_items_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: watchlist_items watchlist_items_watchlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.watchlist_items
    ADD CONSTRAINT watchlist_items_watchlist_id_fkey FOREIGN KEY (watchlist_id) REFERENCES public.watchlists(id) ON DELETE CASCADE;


--
-- Name: watchlists watchlists_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.watchlists
    ADD CONSTRAINT watchlists_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict fs3uXScWfd7aIBYH4gbZLMp6EOX5cPeNteDZgw6jOorcbiDOIRmXoHuri2Y47vi

@"

-- Restaurar hypertables y políticas de TimescaleDB
SELECT create_hypertable('price_ohlcv', 'time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);
ALTER TABLE price_ohlcv SET (timescaledb.compress, timescaledb.compress_segmentby = 'asset_id, timeframe');
SELECT add_compression_policy('price_ohlcv', INTERVAL '7 days', if_not_exists => TRUE);

SELECT create_hypertable('price_ticks', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_retention_policy('price_ticks', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('exchange_rates', 'time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);
"@ | Add-Content -Path ".\database\init\01_schema.sql" -Encoding utf8