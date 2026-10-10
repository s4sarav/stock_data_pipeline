{{ config(materialized='view') }}

with source_data as (
    select * from {{ source('main', 'raw_stocks') }}
)

select
    ticker,
    timestamp as market_timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    -- Add a clean analytical flag: true if the stock closed higher than it opened
    case 
        when close_price > open_price then true 
        else false 
    end as is_positive_day,
    ingested_at
from source_data
