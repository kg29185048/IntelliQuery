import { useState } from 'react'
import './IntentCard.css'

const OPERATORS = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'regex', 'in', 'nin']
const OPERATIONS = ['find', 'aggregate', 'insert', 'update']
const AGG_STAGES  = ['$match', '$group', '$sort', '$limit', '$unwind', '$project', '$lookup']

/**
 * IntentCard — editable confirmation card shown between Phase 1 (intent extraction)
 * and Phase 2 (query generation). The user can inspect and correct every extracted field
 * before running the actual query.
 */
const IntentCard = ({ intent: initialIntent, collections = [], onConfirm, onStartOver }) => {
  const [intent, setIntent] = useState(() => ({
    operation:        initialIntent.operation        || 'find',
    collection:       initialIntent.collection       || '',
    goal:             initialIntent.goal             || '',
    filters:          initialIntent.filters          || [],
    projection:       initialIntent.projection       || [],
    sort:             initialIntent.sort             || null,
    limit:            initialIntent.limit            ?? '',
    aggregate_stages: initialIntent.aggregate_stages || [],
  }))

  // ── helpers ────────────────────────────────────────────────────────────
  const set = (field) => (value) => setIntent(prev => ({ ...prev, [field]: value }))

  const updateFilter = (idx, key, value) =>
    setIntent(prev => ({
      ...prev,
      filters: prev.filters.map((f, i) => i === idx ? { ...f, [key]: value } : f),
    }))

  const addFilter = () =>
    setIntent(prev => ({
      ...prev,
      filters: [...prev.filters, { field: '', operator: 'eq', value: '' }],
    }))

  const removeFilter = (idx) =>
    setIntent(prev => ({ ...prev, filters: prev.filters.filter((_, i) => i !== idx) }))

  const toggleStage = (stage) =>
    setIntent(prev => ({
      ...prev,
      aggregate_stages: prev.aggregate_stages.includes(stage)
        ? prev.aggregate_stages.filter(s => s !== stage)
        : [...prev.aggregate_stages, stage],
    }))

  const handleConfirm = () => {
    const clean = {
      ...intent,
      limit: intent.limit !== '' ? parseInt(intent.limit) || null : null,
    }
    onConfirm(clean)
  }

  const isAggregate = intent.operation === 'aggregate'

  return (
    <div className="intent-card">
      <div className="intent-card__header">
        <span className="intent-card__icon">🧠</span>
        <div>
          <div className="intent-card__title">Here's what I understood</div>
          <div className="intent-card__subtitle">Review and edit before running the query</div>
        </div>
      </div>

      {/* Operation */}
      <div className="intent-row">
        <label className="intent-label">Operation</label>
        <div className="intent-op-tabs">
          {OPERATIONS.map(op => (
            <button
              key={op}
              className={`intent-op-tab ${intent.operation === op ? 'intent-op-tab--active' : ''}`}
              onClick={() => set('operation')(op)}
              type="button"
            >
              {op}
            </button>
          ))}
        </div>
      </div>

      {/* Collection */}
      <div className="intent-row">
        <label className="intent-label">Collection</label>
        {collections.length > 0 ? (
          <select
            className="intent-select"
            value={intent.collection}
            onChange={e => set('collection')(e.target.value)}
          >
            <option value="">— pick a collection —</option>
            {collections.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        ) : (
          <input
            className="intent-input"
            value={intent.collection}
            onChange={e => set('collection')(e.target.value)}
            placeholder="collection name"
          />
        )}
      </div>

      {/* Goal */}
      <div className="intent-row intent-row--col">
        <label className="intent-label">Goal <span className="intent-hint">(what you want)</span></label>
        <textarea
          className="intent-textarea"
          rows={2}
          value={intent.goal}
          onChange={e => set('goal')(e.target.value)}
          placeholder="Describe what you want in plain English…"
        />
      </div>

      {/* Filters */}
      {(intent.operation === 'find' || intent.operation === 'update' || intent.operation === 'aggregate') && (
        <div className="intent-section">
          <div className="intent-section-title">
            Filters
            <span className="intent-hint"> (conditions the LLM extracted)</span>
          </div>

          {intent.filters.length === 0 && (
            <div className="intent-empty-filters">No filters — query will return all documents</div>
          )}

          {intent.filters.map((f, idx) => (
            <div key={idx} className="intent-filter-row">
              <input
                className="intent-input intent-input--field"
                value={f.field}
                onChange={e => updateFilter(idx, 'field', e.target.value)}
                placeholder="field"
              />
              <select
                className="intent-select intent-select--op"
                value={f.operator}
                onChange={e => updateFilter(idx, 'operator', e.target.value)}
              >
                {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
              </select>
              <input
                className="intent-input intent-input--value"
                value={f.value}
                onChange={e => updateFilter(idx, 'value', e.target.value)}
                placeholder="value"
              />
              <button
                className="intent-remove-btn"
                onClick={() => removeFilter(idx)}
                type="button"
                title="Remove filter"
              >✕</button>
            </div>
          ))}

          <button className="intent-add-filter-btn" onClick={addFilter} type="button">
            + Add filter
          </button>
        </div>
      )}

      {/* Aggregation Stages */}
      {isAggregate && (
        <div className="intent-section">
          <div className="intent-section-title">
            Pipeline Stages
            <span className="intent-hint"> (toggle to include/exclude)</span>
          </div>
          <div className="intent-stages">
            {AGG_STAGES.map(stage => (
              <button
                key={stage}
                className={`intent-stage-chip ${intent.aggregate_stages.includes(stage) ? 'intent-stage-chip--active' : ''}`}
                onClick={() => toggleStage(stage)}
                type="button"
              >
                {intent.aggregate_stages.includes(stage) ? '✓ ' : ''}{stage}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Sort + Limit (find / aggregate) */}
      {(intent.operation === 'find' || intent.operation === 'aggregate') && (
        <div className="intent-row intent-row--inline">
          <div className="intent-field-group">
            <label className="intent-label">Sort by</label>
            <input
              className="intent-input"
              value={intent.sort?.field || ''}
              onChange={e => set('sort')({ ...intent.sort, field: e.target.value })}
              placeholder="field name"
            />
            <select
              className="intent-select"
              value={intent.sort?.direction || 'asc'}
              onChange={e => set('sort')({ ...intent.sort, direction: e.target.value })}
            >
              <option value="asc">asc ↑</option>
              <option value="desc">desc ↓</option>
            </select>
          </div>
          <div className="intent-field-group">
            <label className="intent-label">Limit</label>
            <input
              className="intent-input intent-input--limit"
              type="number"
              min={1}
              max={500}
              value={intent.limit}
              onChange={e => set('limit')(e.target.value)}
              placeholder="e.g. 10"
            />
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="intent-actions">
        <button className="intent-btn intent-btn--confirm" onClick={handleConfirm} type="button">
          ✅ Confirm & Run
        </button>
        <button className="intent-btn intent-btn--reset" onClick={onStartOver} type="button">
          ✏️ Start Over
        </button>
      </div>
    </div>
  )
}

export default IntentCard
