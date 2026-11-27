INSERT INTO asset_classes (code, name) VALUES
    ('stock', 'Acciones'),
    ('etf', 'ETFs'),
    ('crypto', 'Criptomonedas'),
    ('bond', 'Bonos'),
    ('cedear', 'CEDEARs'),
    ('forex', 'Divisas'),
    ('commodity', 'Commodities'),
    ('index', 'Índices'),
    ('option', 'Opciones'),
    ('future', 'Futuros')
ON CONFLICT (code) DO NOTHING;

INSERT INTO exchanges (code, name, country, currency, timezone) VALUES
    ('NASDAQ', 'NASDAQ Stock Market', 'US', 'USD', 'America/New_York'),
    ('NYSE', 'New York Stock Exchange', 'US', 'USD', 'America/New_York'),
    ('BCBA', 'Bolsas y Mercados Argentinos', 'AR', 'ARS', 'America/Argentina/Buenos_Aires'),
    ('BINANCE', 'Binance Spot', 'GLB', 'USDT', 'UTC')
ON CONFLICT (code) DO NOTHING;

INSERT INTO assets (id, symbol, name, exchange_id, asset_class_id, currency, is_active, is_argentine)
SELECT uuid_generate_v4(), v.symbol, v.name, e.id, ac.id, v.currency, TRUE, v.is_arg
FROM (VALUES
    ('BTCUSDT', 'Bitcoin', 'BINANCE', 'crypto', 'USD', FALSE),
    ('ETHUSDT', 'Ethereum', 'BINANCE', 'crypto', 'USD', FALSE),
    ('BNBUSDT', 'BNB', 'BINANCE', 'crypto', 'USD', FALSE),
    ('SOLUSDT', 'Solana', 'BINANCE', 'crypto', 'USD', FALSE),
    ('ADAUSDT', 'Cardano', 'BINANCE', 'crypto', 'USD', FALSE),
    ('AAPL', 'Apple Inc.', 'NASDAQ', 'stock', 'USD', FALSE),
    ('MSFT', 'Microsoft Corporation', 'NASDAQ', 'stock', 'USD', FALSE),
    ('NVDA', 'NVIDIA Corporation', 'NASDAQ', 'stock', 'USD', FALSE),
    ('SPY', 'SPDR S&P 500 ETF Trust', 'NYSE', 'etf', 'USD', FALSE),
    ('GGAL.BA', 'Grupo Financiero Galicia', 'BCBA', 'stock', 'ARS', TRUE),
    ('YPFD.BA', 'YPF S.A.', 'BCBA', 'stock', 'ARS', TRUE)
) AS v(symbol, name, ex_code, ac_code, currency, is_arg)
JOIN exchanges e ON e.code = v.ex_code
JOIN asset_classes ac ON ac.code = v.ac_code
ON CONFLICT (symbol, exchange_id) DO NOTHING;
