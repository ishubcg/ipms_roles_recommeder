import { useEffect, useMemo, useState } from 'react'
import { fetchBootstrap, fetchRecommendations, fetchVerticals } from './api'

const STEP_ORDER = ['level', 'vertical', 'daily_work', 'primary_role', 'secondary_roles', 'output']
const STEP_LABELS = {
  level: 'Office Level',
  vertical: 'Vertical',
  daily_work: 'Daily Work',
  primary_role: 'Primary Role',
  secondary_roles: 'Secondary Roles',
  output: 'Summary',
}

function isBaLevel(level) {
  const normalized = String(level || '').trim().toLowerCase()
  return normalized === 'ba' || normalized === 'ba office'
}

function roleToken(role) {
  return `${role.level}|||${role.vertical}|||${role.role}`
}

function toSummaryRows(primaryRole, secondaryRoles) {
  const rows = []
  const allRoles = [
    ...(primaryRole ? [{ ...primaryRole, roleType: 'Primary' }] : []),
    ...secondaryRoles.map((role) => ({ ...role, roleType: 'Secondary' })),
  ]

  allRoles.forEach((role) => {
    role.kpis.forEach((kpi) => {
      rows.push({
        roleType: role.roleType,
        vertical: role.vertical,
        level: role.level,
        roleName: role.role,
        shortRoleName: role.short_role_name || '',
        roleDescription: role.role_description || '',
        kpi: kpi.kpi,
        shortKpi: kpi.short_kpi || '',
      })
    })
  })

  return rows
}

function downloadCsv(rows) {
  const headers = [
    'Role Type',
    'Vertical',
    'Level',
    'Role Name',
    'Short Role Name',
    'Role Description',
    'KPI',
    'Short KPIs',
  ]
  const lines = [headers.join(',')]

  rows.forEach((row) => {
    const values = [
      row.roleType,
      row.vertical,
      row.level,
      row.roleName,
      row.shortRoleName,
      row.roleDescription,
      row.kpi,
      row.shortKpi,
    ].map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`)
    lines.push(values.join(','))
  })

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'kpi_summary.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function ProgressBar({ step }) {
  const currentIndex = STEP_ORDER.indexOf(step)
  const percent = (currentIndex / (STEP_ORDER.length - 1)) * 100

  return (
    <div className="progress-card">
      <div className="progress-title">Your progress</div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="progress-steps">
        {STEP_ORDER.map((stepKey, idx) => {
          const className =
            idx < currentIndex
              ? 'progress-step done'
              : idx === currentIndex
                ? 'progress-step active'
                : 'progress-step'
          return (
            <div key={stepKey} className={className}>
              {idx < currentIndex ? '✓ ' : ''}
              {STEP_LABELS[stepKey]}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SelectedRoles({ level, vertical, primaryRole, secondaryRoles }) {
  if (!level && !vertical && !primaryRole && secondaryRoles.length === 0) return null

  return (
    <div className="selected-chip-wrap">
      {level ? <span className="selected-chip">Level: {level}</span> : null}
      {vertical ? <span className="selected-chip">Vertical: {vertical}</span> : null}
      {primaryRole ? <span className="selected-chip primary">★ {primaryRole.role}</span> : null}
      {secondaryRoles.map((role) => (
        <span className="selected-chip" key={`secondary-chip-${roleToken(role)}`}>
          {role.role}
        </span>
      ))}
    </div>
  )
}

function RoleRecommendationTable({
  roles,
  selectedToken = '',
  selectedTokens = [],
  multiSelect = false,
  maxSelections = 1,
  onSelect,
  filterText,
  onFilterChange,
  title,
  helperText,
}) {
  const filteredRoles = useMemo(() => {
    const query = String(filterText || '').trim().toLowerCase()
    if (!query) return roles
    return roles.filter((role) => role.role.toLowerCase().includes(query))
  }, [roles, filterText])

  return (
    <div className="section-card">
      <div className="section-title">{title}</div>
      {helperText ? <div className="helper-text">{helperText}</div> : null}

      <div className="field-group compact-bottom">
        <label className="field-label">Filter by role name</label>
        <input
          className="text-input"
          placeholder="Type role name"
          value={filterText}
          onChange={(event) => onFilterChange(event.target.value)}
        />
      </div>

      <div className="role-grid role-grid-header">
        <div className="grid-header">Select</div>
        <div className="grid-header">#</div>
        <div className="grid-header">Role Name</div>
        <div className="grid-header">Recommended KPIs</div>
      </div>

      {filteredRoles.length === 0 ? (
        <div className="empty-state">No roles match the current filter.</div>
      ) : (
        filteredRoles.map((role, index) => {
          const token = roleToken(role)
          const isSelected = multiSelect
            ? selectedTokens.includes(token)
            : token === selectedToken

          const disableNewSelection =
            multiSelect &&
            !isSelected &&
            selectedTokens.length >= maxSelections

          return (
            <div className="role-grid role-grid-row" key={token}>
              <div className={`grid-cell select-cell ${isSelected ? 'selected' : ''}`}>
                <button
                  className={`select-button ${isSelected ? 'selected' : ''}`}
                  onClick={() => onSelect(token)}
                  disabled={disableNewSelection}
                >
                  {isSelected ? 'Selected' : 'Select'}
                </button>
              </div>

              <div className={`grid-cell number-cell ${isSelected ? 'selected' : ''}`}>
                <span className="row-number">{index + 1}</span>
              </div>

              <div className={`grid-cell role-name-cell ${isSelected ? 'selected' : ''}`}>
                <div>
                  <div className="role-title">{role.role}</div>
                  <div className="role-meta">{role.vertical} • {role.level}</div>
                  {role.reason ? <div className="role-reason">{role.reason}</div> : null}
                  <div className="role-score">Relevance: {Math.round(role.relevance_score || 0)}%</div>
                </div>
              </div>

              <div className={`grid-cell kpi-cell ${isSelected ? 'selected' : ''}`}>
                <ol className="kpi-list">
                  {role.kpis.map((kpi, idx) => (
                    <li key={`${token}-${idx}`}>{kpi.kpi}</li>
                  ))}
                </ol>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}

function SummaryTable({ rows }) {
  if (rows.length === 0) return null

  return (
    <div className="summary-table-wrap">
      <div className="summary-table-scroll">
        <div className="summary-grid summary-table-header">
          <div>Role Type</div>
          <div>Vertical</div>
          <div>Level</div>
          <div>Role Name</div>
          <div>Short Role Name</div>
          <div>Role Description</div>
          <div>KPI</div>
          <div>Short KPIs</div>
        </div>

        {rows.map((row, index) => (
          <div className="summary-grid summary-row" key={`${row.roleName}-${index}`}>
            <div>{row.roleType}</div>
            <div>{row.vertical}</div>
            <div>{row.level}</div>
            <div>{row.roleName}</div>
            <div>{row.shortRoleName}</div>
            <div>{row.roleDescription}</div>
            <div>{row.kpi}</div>
            <div>{row.shortKpi}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StepPrompt({ text }) {
  return (
    <div className="chat-prompt-card">
      <div className="prompt-label">Assistant</div>
      <div className="prompt-text">{text}</div>
    </div>
  )
}

export default function App() {
  const [step, setStep] = useState('level')
  const [levels, setLevels] = useState([])
  const [verticals, setVerticals] = useState([])
  const [maxSecondaryRoles, setMaxSecondaryRoles] = useState(4)

  const [level, setLevel] = useState('')
  const [vertical, setVertical] = useState('')
  const [dailyWork, setDailyWork] = useState('')

  const [primaryRecommendations, setPrimaryRecommendations] = useState([])
  const [primaryFilter, setPrimaryFilter] = useState('')
  const [selectedPrimaryToken, setSelectedPrimaryToken] = useState('')
  const [usedLlmForPrimary, setUsedLlmForPrimary] = useState(false)
  const [primaryRole, setPrimaryRole] = useState(null)

  const [secondaryVertical, setSecondaryVertical] = useState('')
  const [secondaryRecommendations, setSecondaryRecommendations] = useState([])
  const [secondaryFilter, setSecondaryFilter] = useState('')
  const [selectedSecondaryTokens, setSelectedSecondaryTokens] = useState([])
  const [secondaryRoles, setSecondaryRoles] = useState([])
  const [usedLlmForSecondary, setUsedLlmForSecondary] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const summaryRows = useMemo(() => toSummaryRows(primaryRole, secondaryRoles), [primaryRole, secondaryRoles])

  useEffect(() => {
    async function loadBootstrap() {
      try {
        const data = await fetchBootstrap()
        setLevels(data.levels || [])
        setMaxSecondaryRoles(data.max_secondary_roles || 4)
      } catch (err) {
        setError(err.message || 'Unable to load application bootstrap data.')
      }
    }
    loadBootstrap()
  }, [])

  const selectedPrimaryRole = useMemo(
    () => primaryRecommendations.find((role) => roleToken(role) === selectedPrimaryToken) || null,
    [primaryRecommendations, selectedPrimaryToken],
  )

  const selectedSecondaryRolesFromCurrentView = useMemo(
    () =>
      secondaryRecommendations.filter((role) =>
        selectedSecondaryTokens.includes(roleToken(role))
      ),
    [secondaryRecommendations, selectedSecondaryTokens],
  )

  async function loadVerticals(nextLevel) {
    const response = await fetchVerticals(nextLevel)
    setVerticals(response.verticals || [])
  }

  async function handleLevelContinue() {
    if (!level) {
      setError('Please select an office level.')
      return
    }

    setError('')
    setLoading(true)

    try {
      await loadVerticals(level)
      setVertical('')
      setStep('vertical')
    } catch (err) {
      setError(err.message || 'Unable to load verticals.')
    } finally {
      setLoading(false)
    }
  }

  function handleVerticalContinue() {
    if (!vertical) {
      setError('Please select a vertical.')
      return
    }

    setError('')
    setStep('daily_work')
  }

  async function generateRecommendations(targetVertical, excludeRoles = []) {
    const response = await fetchRecommendations({
      level,
      vertical: targetVertical,
      daily_work: dailyWork,
      exclude_roles: excludeRoles,
    })
    return response
  }

  async function handleGeneratePrimaryRecommendations() {
    if (!dailyWork.trim()) {
      setError('Please describe the work you do on a daily basis.')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await generateRecommendations(vertical, [])
      setPrimaryRecommendations(response.recommendations || [])
      setUsedLlmForPrimary(Boolean(response.used_llm))
      setSelectedPrimaryToken('')
      setPrimaryFilter('')
      setStep('primary_role')
    } catch (err) {
      setError(err.message || 'Unable to generate role recommendations.')
    } finally {
      setLoading(false)
    }
  }

  async function handleConfirmPrimaryRole() {
    if (!selectedPrimaryRole) {
      setError('Please select one primary role.')
      return
    }

    setError('')
    setPrimaryRole(selectedPrimaryRole)
    setSelectedPrimaryToken('')
    setSecondaryRoles([])
    setSecondaryFilter('')
    setSelectedSecondaryTokens([])

    if (isBaLevel(level)) {
      const nextVertical = vertical
      setSecondaryVertical(nextVertical)
      setLoading(true)

      try {
        const response = await generateRecommendations(nextVertical, [selectedPrimaryRole.role])
        setSecondaryRecommendations(response.recommendations || [])
        setUsedLlmForSecondary(Boolean(response.used_llm))
      } catch (err) {
        setError(err.message || 'Unable to prepare secondary recommendations.')
      } finally {
        setLoading(false)
      }
    } else {
      setSecondaryVertical(vertical)
      setSecondaryRecommendations(
        primaryRecommendations.filter((role) => role.role !== selectedPrimaryRole.role)
      )
      setUsedLlmForSecondary(usedLlmForPrimary)
    }

    setStep('secondary_roles')
  }

  async function refreshSecondaryRecommendations(nextVertical = secondaryVertical || vertical) {
    const excludeRoles = [
      ...(primaryRole ? [primaryRole.role] : []),
      ...secondaryRoles.map((role) => role.role),
    ]

    setLoading(true)
    setError('')

    try {
      const response = await generateRecommendations(nextVertical, excludeRoles)
      setSecondaryRecommendations(response.recommendations || [])
      setUsedLlmForSecondary(Boolean(response.used_llm))
      setSelectedSecondaryTokens([])
    } catch (err) {
      setError(err.message || 'Unable to refresh secondary recommendations.')
    } finally {
      setLoading(false)
    }
  }

  function toggleSecondaryRoleSelection(token) {
    setSelectedSecondaryTokens((prev) => {
      if (prev.includes(token)) {
        return prev.filter((item) => item !== token)
      }

      const remainingSlots = maxSecondaryRoles - secondaryRoles.length
      if (prev.length >= remainingSlots) {
        return prev
      }

      return [...prev, token]
    })
  }

  function getUniqueSelectedSecondaryRoles() {
    const existingRoleKeys = new Set(
      secondaryRoles.map((role) => `${role.role}|||${role.vertical}`)
    )

    return selectedSecondaryRolesFromCurrentView.filter(
      (role) => !existingRoleKeys.has(`${role.role}|||${role.vertical}`)
    )
  }

  async function handleAddSecondaryRole() {
    if (selectedSecondaryRolesFromCurrentView.length === 0) {
      setError('Please select at least one secondary role.')
      return
    }

    const uniqueNewRoles = getUniqueSelectedSecondaryRoles()

    if (uniqueNewRoles.length === 0) {
      setError('The selected secondary roles are already added.')
      return
    }

    const totalAfterAdd = secondaryRoles.length + uniqueNewRoles.length
    if (totalAfterAdd > maxSecondaryRoles) {
      setError(`You can add up to ${maxSecondaryRoles} secondary roles in total.`)
      return
    }

    const nextSecondaryRoles = [...secondaryRoles, ...uniqueNewRoles]
    setSecondaryRoles(nextSecondaryRoles)
    setSelectedSecondaryTokens([])
    setError('')

    if (isBaLevel(level)) {
      await refreshSecondaryRecommendations(secondaryVertical || vertical)
    } else {
      const excluded = new Set(
        [primaryRole?.role, ...nextSecondaryRoles.map((role) => role.role)].filter(Boolean)
      )
      setSecondaryRecommendations(
        primaryRecommendations.filter((role) => !excluded.has(role.role))
      )
    }
  }

  function handleFinishSelection() {
    const uniqueNewRoles = getUniqueSelectedSecondaryRoles()

    if (secondaryRoles.length + uniqueNewRoles.length > maxSecondaryRoles) {
      setError(`You can add up to ${maxSecondaryRoles} secondary roles in total.`)
      return
    }

    const nextSecondaryRoles = [...secondaryRoles, ...uniqueNewRoles]
    setSecondaryRoles(nextSecondaryRoles)
    setSelectedSecondaryTokens([])
    setError('')
    setStep('output')
  }

  function handleRestart() {
    setStep('level')
    setLevel('')
    setVertical('')
    setDailyWork('')
    setPrimaryRecommendations([])
    setPrimaryFilter('')
    setSelectedPrimaryToken('')
    setUsedLlmForPrimary(false)
    setPrimaryRole(null)
    setSecondaryVertical('')
    setSecondaryRecommendations([])
    setSecondaryFilter('')
    setSelectedSecondaryTokens([])
    setSecondaryRoles([])
    setUsedLlmForSecondary(false)
    setError('')
  }

  const remainingSecondarySlots = maxSecondaryRoles - secondaryRoles.length

  return (
    <div className="app-page">
      <div className="app-shell">
        <header className="hero-card">
          <div className="hero-copy">
            <div className="hero-badge">Roles and KPIs Selector</div>
            <h1>IPMS Role Recommender</h1>
            <p>
              Select your office level and vertical, describe what you do every day, and get role recommendations powered by AI.
            </p>
          </div>
        </header>

        <ProgressBar step={step} />

        <SelectedRoles
          level={level}
          vertical={vertical}
          primaryRole={primaryRole}
          secondaryRoles={secondaryRoles}
        />

        {error ? <div className="alert error">{error}</div> : null}
        {loading ? <div className="alert info">Working on it...</div> : null}

        {step === 'level' && (
          <div className="section-card">
            <div className="section-title">Step 1 of 5 — Office Level</div>
            <StepPrompt text="Please select your office level." />
            <div className="field-group">
              <label className="field-label">Select your office level</label>
              <select className="select-input" value={level} onChange={(event) => setLevel(event.target.value)}>
                <option value="">Choose a level</option>
                {levels.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary-action" onClick={handleLevelContinue}>Continue →</button>
          </div>
        )}

        {step === 'vertical' && (
          <div className="section-card">
            <div className="section-title">Step 2 of 5 — Business Vertical</div>
            <StepPrompt text="Please select your business vertical." />
            <div className="field-group">
              <label className="field-label">Select your business vertical</label>
              <select className="select-input" value={vertical} onChange={(event) => setVertical(event.target.value)}>
                <option value="">Choose a vertical</option>
                {verticals.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary-action" onClick={handleVerticalContinue}>Continue →</button>
          </div>
        )}

        {step === 'daily_work' && (
          <div className="section-card">
            <div className="section-title">Step 3 of 5 — Daily Work</div>
            <StepPrompt text="What work do you do on daily basis?" />
            <div className="field-group">
              <label className="field-label">Your response</label>
              <textarea
                className="chat-input"
                rows={6}
                placeholder="Describe the work you handle every day. Mention tasks, responsibilities, keywords, teams, delivery themes, complaints, sales, provisioning, assurance, operations, governance, or anything relevant."
                value={dailyWork}
                onChange={(event) => setDailyWork(event.target.value)}
              />
            </div>
            <button className="primary-action" onClick={handleGeneratePrimaryRecommendations}>
              Generate role recommendations →
            </button>
          </div>
        )}

        {step === 'primary_role' && (
          <>
            <div className="section-card compact-card">
              <div className="section-title">Step 4 of 5 — Recommended Primary Roles</div>
              <StepPrompt text="Here are the recommended primary roles based on your daily work. Please select one primary role." />
              <div className="helper-text">
                Review the recommended roles for <strong>{vertical}</strong>.{' '}
                {usedLlmForPrimary
                  ? 'Recommendations were generated using the configured LLM.'
                  : 'Recommendations are using the fallback KPI similarity engine.'}
              </div>
            </div>

            <button className="primary-action success-action" onClick={handleConfirmPrimaryRole}>
              Confirm Primary Role →
            </button>

            <RoleRecommendationTable
              roles={primaryRecommendations}
              selectedToken={selectedPrimaryToken}
              selectedTokens={[]}
              multiSelect={false}
              maxSelections={1}
              onSelect={setSelectedPrimaryToken}
              filterText={primaryFilter}
              onFilterChange={setPrimaryFilter}
              title="Primary role recommendations"
              helperText="Filter the recommended list by role name if needed, then select exactly one primary role."
            />
          </>
        )}

        {step === 'secondary_roles' && (
          <>
            <div className="section-card">
              <div className="section-title">Step 5 of 5 — Secondary Roles</div>
              <StepPrompt text="You can now add secondary roles. Please select any additional roles that apply to your work." />
              <div className="helper-text">
                Add up to {maxSecondaryRoles} secondary roles. For BA levels, you can select a different vertical and refresh recommendations for each additional role.
              </div>

              <div className="selection-limit-note">
                You can still select up to {remainingSecondarySlots} more secondary role(s).
              </div>

              {isBaLevel(level) ? (
                <div className="secondary-toolbar">
                  <div className="field-group slim-field">
                    <label className="field-label">Vertical for this secondary role</label>
                    <select
                      className="select-input"
                      value={secondaryVertical}
                      onChange={(event) => setSecondaryVertical(event.target.value)}
                    >
                      {verticals.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    className="secondary-action"
                    onClick={() => refreshSecondaryRecommendations(secondaryVertical || vertical)}
                  >
                    Refresh recommendations
                  </button>
                </div>
              ) : (
                <div className="helper-pill">Secondary roles will be recommended inside {vertical}.</div>
              )}
            </div>

            <div className="action-row">
              <button className="primary-action success-action" onClick={handleAddSecondaryRole}>
                Confirm Secondary Role(s)
              </button>
              <button className="secondary-action success-outline-action" onClick={handleFinishSelection}>
                Done — Show Summary
              </button>
            </div>

            <RoleRecommendationTable
              roles={secondaryRecommendations}
              selectedToken=""
              selectedTokens={selectedSecondaryTokens}
              multiSelect={true}
              maxSelections={remainingSecondarySlots}
              onSelect={toggleSecondaryRoleSelection}
              filterText={secondaryFilter}
              onFilterChange={setSecondaryFilter}
              title="Secondary role recommendations"
              helperText={
                usedLlmForSecondary
                  ? `Choose up to ${remainingSecondarySlots} secondary role(s) from the recommended list below.`
                  : `Choose up to ${remainingSecondarySlots} secondary role(s) from the similarity-based recommendation list below.`
              }
            />
          </>
        )}

        {step === 'output' && (
          <div className="section-card">
            <div className="section-title">Final Summary</div>
            <div className="summary-intro">
              You selected {primaryRole ? 1 + secondaryRoles.length : secondaryRoles.length} role(s).
            </div>

            {[
              ...(primaryRole ? [{ ...primaryRole, roleType: 'Primary' }] : []),
              ...secondaryRoles.map((role) => ({ ...role, roleType: 'Secondary' })),
            ].map((role) => (
              <div className="output-card" key={`${roleToken(role)}-${role.roleType}`}>
                <div className="output-top">
                  <div className="output-role">{role.role}</div>
                  <div className={`output-badge ${role.roleType.toLowerCase()}`}>{role.roleType}</div>
                </div>
                <div className="output-meta">{role.level} • {role.vertical}</div>
                <ol className="kpi-list output-kpi-list">
                  {role.kpis.map((kpi, idx) => (
                    <li key={`${roleToken(role)}-summary-${idx}`}>{kpi.kpi}</li>
                  ))}
                </ol>
              </div>
            ))}

            <div className="summary-toolbar">
              <h3>Eligible KPI Summary Table</h3>
              <h3>Please Select 5-6 KPIs to submit in IPMS Portal</h3>
              <button className="secondary-action" onClick={() => downloadCsv(summaryRows)}>
                Download CSV
              </button>
            </div>

            <SummaryTable rows={summaryRows} />

            <div className="restart-button-wrap">
              <button className="primary-action" onClick={handleRestart}>Start Over</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}