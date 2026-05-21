-- =============================================================================
-- PLATAFORMA DE ANÁLISIS FINANCIERO E INTELIGENCIA DE INVERSIÓN
-- Esquema completo: PostgreSQL 15 + TimescaleDB 2.x
-- =============================================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- búsqueda fuzzy en símbolos
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- índices compuestos GIN


-- =============================================================================
-- BLOQUE 1: USUARIOS Y AUTENTICACIÓN
-- =============================================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    full_name       VARCHAR(255),
    phone           VARCHAR(30),
    country         VARCHAR(5) DEFAULT 'AR',
    plan            VARCHAR(20) DEFAULT 'free'
                        CHECK (plan IN ('free', 'pro', 'enterprise')),
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   TEXT UNIQUE NOT NULL,
    device_info     JSONB,
    ip_address      INET,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_preferences (
    user_id             UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_currency    VARCHAR(5) DEFAULT 'ARS',
    risk_profile        VARCHAR(20) DEFAULT 'moderate'
                            CHECK (risk_profile IN ('conservative', 'moderate', 'aggressive')),
    preferred_markets   TEXT[] DEFAULT ARRAY['BYMA','NYSE','NASDAQ'],
    notification_email  BOOLEAN DEFAULT TRUE,
    notification_telegram BOOLEAN DEFAULT FALSE,
    telegram_chat_id    VARCHAR(100),
    notification_whatsapp BOOLEAN DEFAULT FALSE,
    whatsapp_number     VARCHAR(30),
    theme               VARCHAR(10) DEFAULT 'dark',
    language            VARCHAR(5) DEFAULT 'es',
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);


-- =============================================================================
-- BLOQUE 2: ACTIVOS FINANCIEROS (MASTER DATA)
-- =============================================================================

CREATE TABLE asset_classes (
    id      SERIAL PRIMARY KEY,
    code    VARCHAR(30) UNIQUE NOT NULL,  -- 'stock', 'etf', 'bond', 'crypto', etc.
    name    VARCHAR(100) NOT NULL
);

INSERT INTO asset_classes (code, name) VALUES
    ('stock',       'Acciones'),
    ('etf',         'ETF'),
    ('bond',        'Bonos'),
    ('cedear',      'CEDEARs'),
    ('crypto',      'Criptomonedas'),
    ('on',          'Obligaciones Negociables'),
    ('fci',         'Fondos Comunes de Inversión'),
    ('commodity',   'Commodities'),
    ('forex',       'Divisas'),
    ('index',       'Índices Bursátiles');

CREATE TABLE exchanges (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) UNIQUE NOT NULL,  -- 'BYMA', 'NYSE', 'NASDAQ', etc.
    name            VARCHAR(100) NOT NULL,
    country         VARCHAR(5),
    currency        VARCHAR(5),
    timezone        VARCHAR(50),
    open_time       TIME,
    close_time      TIME
);

INSERT INTO exchanges (code, name, country, currency, timezone, open_time, close_time) VALUES
    ('BYMA',    'Bolsa y Mercados Argentinos',   'AR', 'ARS', 'America/Argentina/Buenos_Aires', '11:00', '17:00'),
    ('MAE',     'Mercado Abierto Electrónico',   'AR', 'ARS', 'America/Argentina/Buenos_Aires', '10:00', '17:00'),
    ('NYSE',    'New York Stock Exchange',        'US', 'USD', 'America/New_York',               '09:30', '16:00'),
    ('NASDAQ',  'NASDAQ Stock Market',            'US', 'USD', 'America/New_York',               '09:30', '16:00'),
    ('BINANCE', 'Binance Exchange',               'MT', 'USD', 'UTC',                            '00:00', '23:59'),
    ('COMEX',   'COMEX Commodities',              'US', 'USD', 'America/New_York',               '08:20', '13:30');

CREATE TABLE assets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          VARCHAR(30) NOT NULL,
    exchange_id     INTEGER REFERENCES exchanges(id),
    asset_class_id  INTEGER REFERENCES asset_classes(id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    currency        VARCHAR(5) DEFAULT 'USD',
    isin            VARCHAR(20),
    cuit            VARCHAR(15),          -- para activos argentinos
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    country         VARCHAR(5),
    is_active       BOOLEAN DEFAULT TRUE,
    is_argentine    BOOLEAN DEFAULT FALSE, -- flag para módulo ARG
    underlying_symbol VARCHAR(30),        -- para CEDEARs: símbolo original USA
    ratio           NUMERIC(10,4),        -- ratio de conversión CEDEAR
    metadata        JSONB,               -- datos adicionales variables
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, exchange_id)
);

CREATE INDEX idx_assets_symbol ON assets USING gin(symbol gin_trgm_ops);
CREATE INDEX idx_assets_class ON assets(asset_class_id);
CREATE INDEX idx_assets_exchange ON assets(exchange_id);
CREATE INDEX idx_assets_argentine ON assets(is_argentine) WHERE is_argentine = TRUE;


-- =============================================================================
-- BLOQUE 3: SERIES TEMPORALES (TimescaleDB)
-- =============================================================================

-- Tabla principal de precios OHLCV (hypertable)
CREATE TABLE price_ohlcv (
    time        TIMESTAMPTZ NOT NULL,
    asset_id    UUID NOT NULL REFERENCES assets(id),
    open        NUMERIC(20,6) NOT NULL,
    high        NUMERIC(20,6) NOT NULL,
    low         NUMERIC(20,6) NOT NULL,
    close       NUMERIC(20,6) NOT NULL,
    volume      NUMERIC(24,2) DEFAULT 0,
    vwap        NUMERIC(20,6),           -- Volume Weighted Average Price
    trades      INTEGER,
    source      VARCHAR(30),             -- 'alphavantage', 'byma', 'binance', etc.
    timeframe   VARCHAR(5) NOT NULL,     -- '1m','5m','15m','1h','4h','1d','1w'
    PRIMARY KEY (time, asset_id, timeframe)
);

-- Convertir en hypertable particionada por mes
SELECT create_hypertable('price_ohlcv', 'time',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Compresión automática de datos > 7 días
SELECT add_compression_policy('price_ohlcv', INTERVAL '7 days');

CREATE INDEX idx_price_asset_time ON price_ohlcv(asset_id, time DESC, timeframe);

-- Cotizaciones en tiempo real (tick data, rotación rápida)
CREATE TABLE price_ticks (
    time        TIMESTAMPTZ NOT NULL,
    asset_id    UUID NOT NULL REFERENCES assets(id),
    price       NUMERIC(20,6) NOT NULL,
    bid         NUMERIC(20,6),
    ask         NUMERIC(20,6),
    volume      NUMERIC(20,2),
    source      VARCHAR(30),
    PRIMARY KEY (time, asset_id)
);

SELECT create_hypertable('price_ticks', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Retención: solo 30 días de ticks
SELECT add_retention_policy('price_ticks', INTERVAL '30 days');


-- =============================================================================
-- BLOQUE 4: DATOS ECONÓMICOS ARGENTINA
-- =============================================================================

CREATE TABLE arg_economic_indicators (
    id              SERIAL PRIMARY KEY,
    indicator_code  VARCHAR(50) NOT NULL,  -- 'dolar_mep', 'dolar_ccl', 'dolar_blue', 'riesgo_pais', 'inflacion_mensual', etc.
    indicator_name  VARCHAR(100) NOT NULL,
    value           NUMERIC(20,6) NOT NULL,
    unit            VARCHAR(20),           -- 'ARS', 'USD', 'bps', '%'
    period          DATE,                  -- fecha del dato
    source          VARCHAR(50),           -- 'bcra', 'byma', 'ambito', 'cronista'
    metadata        JSONB,
    recorded_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_arg_indicator_code ON arg_economic_indicators(indicator_code, period DESC);

-- Vista materializada: último valor de cada indicador
CREATE MATERIALIZED VIEW arg_latest_indicators AS
SELECT DISTINCT ON (indicator_code)
    indicator_code,
    indicator_name,
    value,
    unit,
    period,
    source,
    recorded_at
FROM arg_economic_indicators
ORDER BY indicator_code, recorded_at DESC;

CREATE UNIQUE INDEX ON arg_latest_indicators(indicator_code);

-- Tipos de cambio históricos (series temporales)
CREATE TABLE exchange_rates (
    time        TIMESTAMPTZ NOT NULL,
    from_currency VARCHAR(5) NOT NULL,
    to_currency   VARCHAR(5) NOT NULL,
    rate          NUMERIC(20,6) NOT NULL,
    rate_type     VARCHAR(20),  -- 'oficial', 'mep', 'ccl', 'blue', 'mayorista'
    source        VARCHAR(30),
    PRIMARY KEY (time, from_currency, to_currency, rate_type)
);

SELECT create_hypertable('exchange_rates', 'time', if_not_exists => TRUE);

-- Licitaciones y deuda pública
CREATE TABLE arg_debt_auctions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_date    DATE NOT NULL,
    instrument      VARCHAR(100) NOT NULL,
    isin            VARCHAR(20),
    cut_rate        NUMERIC(10,4),   -- tasa de corte (%)
    amount_offered  NUMERIC(24,2),
    amount_awarded  NUMERIC(24,2),
    currency        VARCHAR(5),
    maturity_date   DATE,
    source          VARCHAR(30),
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- =============================================================================
-- BLOQUE 5: ANÁLISIS TÉCNICO (RESULTADOS CALCULADOS)
-- =============================================================================

CREATE TABLE technical_indicators (
    id          BIGSERIAL PRIMARY KEY,
    asset_id    UUID NOT NULL REFERENCES assets(id),
    timeframe   VARCHAR(5) NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL,
    -- Tendencia
    ema_9       NUMERIC(20,6),
    ema_21      NUMERIC(20,6),
    ema_50      NUMERIC(20,6),
    ema_200     NUMERIC(20,6),
    sma_20      NUMERIC(20,6),
    sma_50      NUMERIC(20,6),
    sma_200     NUMERIC(20,6),
    -- Momentum
    rsi_14      NUMERIC(8,4),
    macd_line   NUMERIC(20,6),
    macd_signal NUMERIC(20,6),
    macd_hist   NUMERIC(20,6),
    stoch_k     NUMERIC(8,4),
    stoch_d     NUMERIC(8,4),
    -- Volatilidad
    bb_upper    NUMERIC(20,6),
    bb_middle   NUMERIC(20,6),
    bb_lower    NUMERIC(20,6),
    bb_width    NUMERIC(10,6),
    atr_14      NUMERIC(20,6),
    -- Volumen
    vwap        NUMERIC(20,6),
    obv         NUMERIC(24,2),
    -- Señales detectadas (arrays de texto)
    signals     TEXT[],  -- ['oversold', 'macd_bullish_cross', 'bb_squeeze', ...]
    trend       VARCHAR(10) CHECK (trend IN ('bullish', 'bearish', 'neutral', 'sideways')),
    strength    NUMERIC(5,2),  -- 0-100
    UNIQUE (asset_id, timeframe, calculated_at)
);

CREATE INDEX idx_tech_asset_time ON technical_indicators(asset_id, timeframe, calculated_at DESC);

-- Soportes y resistencias detectados automáticamente
CREATE TABLE support_resistance_levels (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id    UUID NOT NULL REFERENCES assets(id),
    timeframe   VARCHAR(5) NOT NULL,
    level_type  VARCHAR(10) CHECK (level_type IN ('support', 'resistance')),
    price       NUMERIC(20,6) NOT NULL,
    strength    NUMERIC(5,2),           -- qué tan fuerte es el nivel (0-100)
    touches     INTEGER DEFAULT 1,      -- cuántas veces rebotó
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);


-- =============================================================================
-- BLOQUE 6: ANÁLISIS FUNDAMENTAL
-- =============================================================================

CREATE TABLE fundamental_data (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id            UUID NOT NULL REFERENCES assets(id),
    period              DATE NOT NULL,             -- trimestre/año
    period_type         VARCHAR(10) DEFAULT 'TTM'
                            CHECK (period_type IN ('Q1','Q2','Q3','Q4','annual','TTM')),
    -- Valuación
    market_cap          NUMERIC(24,2),
    enterprise_value    NUMERIC(24,2),
    pe_ratio            NUMERIC(12,4),
    forward_pe          NUMERIC(12,4),
    pb_ratio            NUMERIC(12,4),
    ps_ratio            NUMERIC(12,4),
    ev_ebitda           NUMERIC(12,4),
    -- Rentabilidad
    revenue             NUMERIC(24,2),
    gross_profit        NUMERIC(24,2),
    ebitda              NUMERIC(24,2),
    net_income          NUMERIC(24,2),
    eps                 NUMERIC(12,4),
    roe                 NUMERIC(10,4),
    roa                 NUMERIC(10,4),
    roic                NUMERIC(10,4),
    -- Liquidez y deuda
    current_ratio       NUMERIC(10,4),
    quick_ratio         NUMERIC(10,4),
    debt_to_equity      NUMERIC(10,4),
    net_debt            NUMERIC(24,2),
    interest_coverage   NUMERIC(10,4),
    -- Crecimiento
    revenue_growth_yoy  NUMERIC(10,4),
    earnings_growth_yoy NUMERIC(10,4),
    -- Dividendos
    dividend_yield      NUMERIC(10,4),
    payout_ratio        NUMERIC(10,4),
    dividend_per_share  NUMERIC(12,4),
    -- Free Cash Flow
    operating_cf        NUMERIC(24,2),
    capex               NUMERIC(24,2),
    free_cash_flow      NUMERIC(24,2),
    -- Scores calculados
    fundamental_score   NUMERIC(5,2),  -- 0-100: qué tan atractivo fundamentalmente
    valuation_score     NUMERIC(5,2),  -- 0-100: subvalorado/sobrevalorado
    quality_score       NUMERIC(5,2),  -- 0-100: calidad del negocio
    source              VARCHAR(30),
    raw_data            JSONB,
    fetched_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (asset_id, period, period_type)
);


-- =============================================================================
-- BLOQUE 7: MOTOR DE IA - SEÑALES Y RECOMENDACIONES
-- =============================================================================

CREATE TABLE ai_models (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    version     VARCHAR(20) NOT NULL,
    model_type  VARCHAR(50),  -- 'xgboost', 'lstm', 'random_forest', 'ensemble', 'nlp'
    asset_class VARCHAR(30),  -- a qué clase de activo aplica
    timeframe   VARCHAR(5),
    is_active   BOOLEAN DEFAULT TRUE,
    accuracy    NUMERIC(6,4),     -- accuracy en test set
    sharpe_backtest NUMERIC(8,4), -- Sharpe del backtest
    trained_at  TIMESTAMPTZ,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id        UUID NOT NULL REFERENCES assets(id),
    model_id        INTEGER REFERENCES ai_models(id),
    signal_type     VARCHAR(20) NOT NULL
                        CHECK (signal_type IN ('buy', 'sell', 'hold', 'watch', 'avoid')),
    strategy        VARCHAR(30),  -- 'swing_trade', 'value', 'momentum', 'arbitrage', 'defensive'
    timeframe       VARCHAR(5),
    -- Scores
    confidence      NUMERIC(5,2) NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    risk_score      NUMERIC(5,2) CHECK (risk_score BETWEEN 0 AND 100),
    reward_score    NUMERIC(5,2) CHECK (reward_score BETWEEN 0 AND 100),
    expected_return NUMERIC(8,4),  -- retorno esperado %
    -- Gestión de riesgo sugerida
    entry_price     NUMERIC(20,6),
    stop_loss       NUMERIC(20,6),
    take_profit_1   NUMERIC(20,6),
    take_profit_2   NUMERIC(20,6),
    risk_reward     NUMERIC(8,4),
    -- Contexto y explicación
    rationale       TEXT,          -- explicación en lenguaje natural
    technical_factors JSONB,       -- qué señales técnicas dispararon
    fundamental_factors JSONB,     -- qué fundamentals aplican
    sentiment_score NUMERIC(5,2),  -- -100 a 100
    -- Estado
    is_active       BOOLEAN DEFAULT TRUE,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    invalidated_at  TIMESTAMPTZ,
    invalidation_reason TEXT
);

CREATE INDEX idx_signals_asset ON ai_signals(asset_id, generated_at DESC) WHERE is_active = TRUE;
CREATE INDEX idx_signals_type ON ai_signals(signal_type, confidence DESC) WHERE is_active = TRUE;

-- Detección de anomalías de mercado
CREATE TABLE market_anomalies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id        UUID NOT NULL REFERENCES assets(id),
    anomaly_type    VARCHAR(50),  -- 'volume_spike', 'price_gap', 'unusual_options', 'news_divergence'
    severity        VARCHAR(10) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description     TEXT,
    detected_value  NUMERIC(20,6),
    expected_range  NUMRANGE,
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB
);


-- =============================================================================
-- BLOQUE 8: NOTICIAS Y SENTIMIENTO DE MERCADO
-- =============================================================================

CREATE TABLE news_articles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          VARCHAR(50) NOT NULL,  -- 'reuters', 'bloomberg', 'ambito', 'cronista', etc.
    headline        TEXT NOT NULL,
    summary         TEXT,
    url             TEXT,
    author          VARCHAR(150),
    published_at    TIMESTAMPTZ NOT NULL,
    -- NLP results
    sentiment_score NUMERIC(5,2),          -- -100 (muy negativo) a 100 (muy positivo)
    sentiment_label VARCHAR(15) CHECK (sentiment_label IN ('very_negative','negative','neutral','positive','very_positive')),
    relevance_score NUMERIC(5,2),          -- qué tan relevante para mercados (0-100)
    topics          TEXT[],                -- ['inflation', 'fed', 'earnings', 'argentina', ...]
    entities        JSONB,                 -- personas, empresas, países detectados
    -- Clasificación adicional
    category        VARCHAR(30),           -- 'macro', 'company', 'crypto', 'argentina', 'commodities'
    is_breaking     BOOLEAN DEFAULT FALSE,
    language        VARCHAR(5) DEFAULT 'es',
    processed_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_sentiment ON news_articles(sentiment_score, published_at DESC);
CREATE INDEX idx_news_topics ON news_articles USING gin(topics);

-- Relación noticias ↔ activos
CREATE TABLE news_asset_mentions (
    news_id     UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    asset_id    UUID NOT NULL REFERENCES assets(id),
    relevance   NUMERIC(5,2),   -- qué tan relevante es la noticia para este activo
    impact_type VARCHAR(10) CHECK (impact_type IN ('positive', 'negative', 'neutral')),
    PRIMARY KEY (news_id, asset_id)
);

-- Agregado de sentimiento por activo (calculado periódicamente)
CREATE TABLE sentiment_aggregates (
    id              BIGSERIAL PRIMARY KEY,
    asset_id        UUID NOT NULL REFERENCES assets(id),
    period_start    TIMESTAMPTZ NOT NULL,
    period_end      TIMESTAMPTZ NOT NULL,
    period_type     VARCHAR(5) CHECK (period_type IN ('1h', '4h', '1d', '1w')),
    sentiment_avg   NUMERIC(5,2),
    sentiment_std   NUMERIC(5,2),
    news_count      INTEGER DEFAULT 0,
    social_score    NUMERIC(5,2),   -- score de redes sociales
    fear_greed_idx  NUMERIC(5,2),   -- índice miedo/codicia local
    UNIQUE (asset_id, period_start, period_type)
);


-- =============================================================================
-- BLOQUE 9: PORTAFOLIOS Y POSICIONES
-- =============================================================================

CREATE TABLE portfolios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    currency        VARCHAR(5) DEFAULT 'USD',
    portfolio_type  VARCHAR(20) DEFAULT 'real'
                        CHECK (portfolio_type IN ('real', 'paper', 'backtest')),
    is_default      BOOLEAN DEFAULT FALSE,
    broker          VARCHAR(50),      -- 'iol', 'balanz', 'interactive_brokers', etc.
    broker_account  VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolio_positions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id        UUID NOT NULL REFERENCES assets(id),
    quantity        NUMERIC(24,8) NOT NULL,
    avg_cost        NUMERIC(20,6) NOT NULL,    -- precio promedio de compra
    currency        VARCHAR(5) DEFAULT 'USD',
    opened_at       TIMESTAMPTZ DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    is_open         BOOLEAN DEFAULT TRUE,
    notes           TEXT,
    UNIQUE (portfolio_id, asset_id) WHERE is_open = TRUE
);

CREATE TABLE portfolio_transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id),
    asset_id        UUID NOT NULL REFERENCES assets(id),
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('buy', 'sell', 'dividend', 'split', 'transfer_in', 'transfer_out')),
    quantity        NUMERIC(24,8) NOT NULL,
    price           NUMERIC(20,6) NOT NULL,
    commission      NUMERIC(12,4) DEFAULT 0,
    currency        VARCHAR(5) DEFAULT 'USD',
    fx_rate         NUMERIC(12,6) DEFAULT 1,   -- tipo de cambio al momento
    notes           TEXT,
    executed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshots diarios del portafolio (para calcular rendimiento histórico)
CREATE TABLE portfolio_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id),
    snapshot_date   DATE NOT NULL,
    total_value_usd NUMERIC(20,4),
    total_value_ars NUMERIC(24,2),
    daily_return    NUMERIC(10,6),
    total_return    NUMERIC(10,6),
    cash_balance    NUMERIC(20,4),
    positions_data  JSONB,   -- snapshot completo de posiciones
    metrics         JSONB,   -- sharpe, max_drawdown, beta, etc.
    UNIQUE (portfolio_id, snapshot_date)
);


-- =============================================================================
-- BLOQUE 10: WATCHLISTS Y ALERTAS
-- =============================================================================

CREATE TABLE watchlists (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE watchlist_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id    UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    asset_id        UUID NOT NULL REFERENCES assets(id),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT,
    UNIQUE (watchlist_id, asset_id)
);

CREATE TABLE alert_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id        UUID REFERENCES assets(id),   -- NULL = alerta global
    alert_name      VARCHAR(100) NOT NULL,
    alert_type      VARCHAR(30) NOT NULL
                        CHECK (alert_type IN (
                            'price_above', 'price_below', 'price_change_pct',
                            'rsi_overbought', 'rsi_oversold',
                            'macd_cross_bullish', 'macd_cross_bearish',
                            'volume_spike', 'bb_breakout',
                            'ai_signal', 'news_sentiment',
                            'arg_dolar_change', 'arg_riesgo_pais',
                            'custom'
                        )),
    condition_value NUMERIC(20,6),
    condition_pct   NUMERIC(8,4),
    timeframe       VARCHAR(5),
    channels        TEXT[] DEFAULT ARRAY['email'],  -- ['email', 'telegram', 'whatsapp', 'push']
    is_active       BOOLEAN DEFAULT TRUE,
    repeat          BOOLEAN DEFAULT FALSE,
    cooldown_minutes INTEGER DEFAULT 60,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alert_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         UUID NOT NULL REFERENCES alert_rules(id),
    asset_id        UUID REFERENCES assets(id),
    triggered_value NUMERIC(20,6),
    message         TEXT NOT NULL,
    channels_sent   TEXT[],
    was_delivered   BOOLEAN DEFAULT FALSE,
    delivery_errors JSONB,
    triggered_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_events_rule ON alert_events(rule_id, triggered_at DESC);


-- =============================================================================
-- BLOQUE 11: BACKTESTING Y SIMULACIÓN
-- =============================================================================

CREATE TABLE backtest_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    name            VARCHAR(150),
    strategy_type   VARCHAR(50),   -- 'macd_crossover', 'rsi_reversal', 'custom', etc.
    asset_ids       UUID[],
    timeframe       VARCHAR(5),
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    initial_capital NUMERIC(20,4) NOT NULL,
    parameters      JSONB NOT NULL,   -- parámetros de la estrategia
    -- Resultados
    final_capital   NUMERIC(20,4),
    total_return    NUMERIC(10,4),
    annualized_return NUMERIC(10,4),
    max_drawdown    NUMERIC(10,4),
    sharpe_ratio    NUMERIC(8,4),
    sortino_ratio   NUMERIC(8,4),
    calmar_ratio    NUMERIC(8,4),
    win_rate        NUMERIC(8,4),
    total_trades    INTEGER,
    winning_trades  INTEGER,
    losing_trades   INTEGER,
    avg_win         NUMERIC(10,4),
    avg_loss        NUMERIC(10,4),
    profit_factor   NUMERIC(8,4),
    status          VARCHAR(15) DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE backtest_trades (
    id              BIGSERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    asset_id        UUID NOT NULL REFERENCES assets(id),
    side            VARCHAR(5) CHECK (side IN ('buy', 'sell')),
    quantity        NUMERIC(20,8),
    entry_price     NUMERIC(20,6),
    exit_price      NUMERIC(20,6),
    entry_time      TIMESTAMPTZ,
    exit_time       TIMESTAMPTZ,
    pnl             NUMERIC(20,6),
    pnl_pct         NUMERIC(10,4),
    exit_reason     VARCHAR(30)   -- 'stop_loss', 'take_profit', 'signal', 'end_of_test'
);


-- =============================================================================
-- BLOQUE 12: GESTIÓN DE RIESGO
-- =============================================================================

CREATE TABLE risk_metrics (
    id              BIGSERIAL PRIMARY KEY,
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id),
    calculated_at   TIMESTAMPTZ NOT NULL,
    -- VaR
    var_95_1d       NUMERIC(10,4),   -- Value at Risk 95% 1 día
    var_99_1d       NUMERIC(10,4),
    cvar_95_1d      NUMERIC(10,4),   -- Conditional VaR (Expected Shortfall)
    -- Portfolio metrics
    sharpe_ratio    NUMERIC(8,4),
    sortino_ratio   NUMERIC(8,4),
    beta            NUMERIC(8,4),    -- vs benchmark (S&P 500 o Merval)
    alpha           NUMERIC(8,4),
    volatility_ann  NUMERIC(10,4),   -- volatilidad anualizada
    max_drawdown    NUMERIC(10,4),
    current_drawdown NUMERIC(10,4),
    -- Concentración
    top1_concentration  NUMERIC(8,4),  -- % del activo más grande
    top5_concentration  NUMERIC(8,4),
    sector_concentration JSONB,
    -- Correlaciones
    avg_correlation NUMERIC(8,4),
    diversification_score NUMERIC(5,2),   -- 0-100
    UNIQUE (portfolio_id, calculated_at)
);


-- =============================================================================
-- BLOQUE 13: AUDITORÍA Y LOGS
-- =============================================================================

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   TEXT,
    ip_address  INET,
    user_agent  TEXT,
    request_data JSONB,
    response_code SMALLINT,
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);

-- Retención de 90 días en logs
CREATE TABLE api_rate_limits (
    id          BIGSERIAL PRIMARY KEY,
    key_type    VARCHAR(20),  -- 'user', 'ip', 'api_key'
    key_value   TEXT NOT NULL,
    endpoint    VARCHAR(100),
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (key_value, endpoint, window_start)
);


-- =============================================================================
-- BLOQUE 14: VISTAS ÚTILES
-- =============================================================================

-- Vista: señales activas con info del activo
CREATE VIEW v_active_signals AS
SELECT
    s.id,
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
FROM ai_signals s
JOIN assets a ON s.asset_id = a.id
JOIN exchanges e ON a.exchange_id = e.id
JOIN asset_classes ac ON a.asset_class_id = ac.id
WHERE s.is_active = TRUE
  AND (s.expires_at IS NULL OR s.expires_at > NOW())
ORDER BY s.confidence DESC, s.generated_at DESC;

-- Vista: últimas cotizaciones por activo
CREATE VIEW v_latest_quotes AS
SELECT DISTINCT ON (asset_id, timeframe)
    asset_id,
    timeframe,
    time AS quote_time,
    open, high, low, close, volume, vwap
FROM price_ohlcv
ORDER BY asset_id, timeframe, time DESC;

-- Vista: resumen de portafolio
CREATE VIEW v_portfolio_summary AS
SELECT
    p.id AS portfolio_id,
    p.user_id,
    p.name,
    p.currency,
    COUNT(pp.id) AS position_count,
    SUM(pp.quantity * pp.avg_cost) AS cost_basis
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.id = pp.portfolio_id AND pp.is_open = TRUE
GROUP BY p.id;


-- =============================================================================
-- BLOQUE 15: TRIGGERS Y FUNCIONES
-- =============================================================================

-- Auto-actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_portfolios_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Función: refrescar vista materializada de indicadores ARG
CREATE OR REPLACE FUNCTION refresh_arg_indicators()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY arg_latest_indicators;
END;
$$ LANGUAGE plpgsql;

-- Función: calcular posición actual de un portafolio
CREATE OR REPLACE FUNCTION get_portfolio_position(p_portfolio_id UUID, p_asset_id UUID)
RETURNS TABLE(quantity NUMERIC, avg_cost NUMERIC, cost_basis NUMERIC) AS $$
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
$$ LANGUAGE plpgsql;