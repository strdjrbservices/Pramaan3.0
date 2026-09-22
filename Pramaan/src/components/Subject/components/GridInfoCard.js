import React from 'react';
import { Paper, Box, Typography, Tooltip, IconButton, LinearProgress } from '@mui/material';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import { EditableField } from './EditableField';

export const GridInfoCard = ({ id, title, fields, data, cardClass = 'bg-secondary', usePre = false, extractionAttempted, onDataChange, editingField, setEditingField, highlightedFields = [], allData, loading, loadingSection, manualValidations, handleManualValidation, onRevisionButtonClick, revisionHandlers, showBlankValidation = false, hideEmptyFields = false }) => {

  const renderNeighborhoodTotal = () => {
    if (id !== 'neighborhood-section' || !data) return null;

    const usageFields = ["One-Unit", "2-4 Unit", "Multi-Family", "Commercial", "Other"];
    const values = usageFields.map(f => {
      const val = String(data[f] || '0').replace('%', '').trim();
      return parseFloat(val) || 0;
    });
    const total = values.reduce((sum, v) => sum + v, 0);

    const totalStyle = {
      fontWeight: 'bold',
      padding: '2px 8px',
      borderRadius: '4px',
      color: total === 100 ? '#000000' : '#721c24',
      backgroundColor: total === 100 ? '#91ff00ff' : '#f8d7da',
    };

    return <span style={totalStyle}>Total: {total}%</span>;
  };

  const getDynamicFields = () => {
    if (id !== 'site-section' || !data) return fields;

    let dynamicFields = [...fields];
    const zoningComplianceValue = data?.['Zoning Compliance'];
    const complianceIndex = dynamicFields.indexOf('Zoning Compliance');

    if (complianceIndex !== -1) {
      if (zoningComplianceValue === 'Legal Nonconforming (Grandfathered Use)' && !dynamicFields.includes('Legal Nonconforming (Grandfathered Use) comment')) {
        dynamicFields.splice(complianceIndex + 1, 0, 'Legal Nonconforming (Grandfathered Use) comment');
      } else if (zoningComplianceValue === 'No Zoning' && !dynamicFields.includes('No Zoning comment')) {
        dynamicFields.splice(complianceIndex + 1, 0, 'No Zoning comment');
      }
    }
    return dynamicFields;
  };
  const cardHeaderColors = {
    'bg-primary': 'primary.main',
    'bg-secondary': 'secondary.main',
    'bg-info': 'info.main',
    'bg-warning': 'warning.main',
    'bg-success': 'success.main',
    'bg-danger': 'error.main',
    'bg-dark': 'grey.900',
  };

  const borderColor = cardHeaderColors[cardClass] || 'primary.main';

  const renderValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      if (value.hasOwnProperty('choice')) {
        return value.choice || '';
      }
      return Object.entries(value).map(([key, val]) => `${key}: ${val}`).join(', ');
    }
    return value || '';
  };

  const renderGridItemValue = (field) => {
    if (!data) return '';
    if (field === 'Garage Att./Det./Built-in') {
      const att = data['Garage Att.'] || data?.IMPROVEMENTS?.['Garage Att.'] || '';
      const det = data['Garage Detached'] || data?.IMPROVEMENTS?.['Garage Detached'] || '';
      const builtin = data['Garage Built-in'] || data?.IMPROVEMENTS?.['Garage Built-in'] || '';
      return [att, det, builtin].filter(Boolean).join(' / ');
    }
    const val = data[field] ?? data?.IMPROVEMENTS?.[field] ?? data?.COST_APPROACH?.[field] ?? data?.INCOME_APPROACH?.[field] ?? data?.PUD_INFO?.[field] ?? data?.SITE?.[field] ?? data?.NEIGHBORHOOD?.[field] ?? data?.SUBJECT?.[field];
    return renderValue(val);
  };

  const renderGridItem = (field) => {
    if (id === 'neighborhood-section' && field === 'Present Land Use for other') {
      if (!data) return null;
      const otherValue = String(data['Other'] || '0').replace('%', '').trim();
      const otherNumericValue = parseFloat(otherValue);

      if (isNaN(otherNumericValue) || otherNumericValue <= 0) {
        return null;
      }
    }

    const isHighlighted = highlightedFields.includes(field);
    let isItemMissing = false;
    return (
      <div key={field} className={`subject-grid-item ${isHighlighted ? 'highlighted-field' : ''}`}>
        <span className="field-label">{field}</span>
        <EditableField
          fieldPath={(() => {
            const baseFieldPath = Array.isArray(field) ? field : [field];

            return onDataChange.length === 2 ? baseFieldPath : [id.replace('-section', '').toUpperCase(), ...baseFieldPath];
          })()}
          value={data ? renderGridItemValue(field) : ''}
          onDataChange={onDataChange}
          editingField={editingField}
          setEditingField={setEditingField}
          usePre={usePre}
          isMissing={isItemMissing}
          inputClassName={`form-control form-control-sm ${usePre ? "field-value-pre" : "field-value"}`}
          isEditable={true}
          allData={allData}
          manualValidations={manualValidations}
          handleManualValidation={handleManualValidation} revisionHandlers={revisionHandlers}
          showBlankValidation={showBlankValidation}
          inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, height: 'auto', resize: usePre ? 'vertical' : 'none' }}
        />
      </div>
    );
  };

  const renderCertField = (label, fieldPath, isCheckbox = false) => {
    if (isCheckbox) {
      const isChecked = data && (data[fieldPath] === 'Yes' || data[fieldPath] === true || String(data[fieldPath]).toLowerCase() === 'x');
      const handleToggle = () => {
        const newValue = isChecked ? 'No' : 'Yes';
        onDataChange([fieldPath], newValue);
      };
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '4px 0' }}>
          <input
            type="checkbox"
            checked={isChecked}
            onChange={handleToggle}
            style={{ width: '14px', height: '14px', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '0.75rem', fontWeight: '500', color: '#495057' }}>{label}</span>
        </div>
      );
    }

    return (
      <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '100px', whiteSpace: 'nowrap' }}>{label}</span>
          <div style={{ flexGrow: 1 }}>
            <EditableField
              fieldPath={[fieldPath]}
              value={data ? renderValue(data[fieldPath]) : ''}
              onDataChange={onDataChange}
              editingField={editingField}
              setEditingField={setEditingField}
              isMissing={false}
              isEditable={true}
              allData={allData}
              manualValidations={manualValidations}
              handleManualValidation={handleManualValidation}
              revisionHandlers={revisionHandlers}
              inputClassName="form-control form-control-sm field-value"
              inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderCostField = (label, fieldPath) => {
    const costData = data?.COST_APPROACH || data || {};
    const val = costData?.[fieldPath] ?? costData?.[label] ?? data?.COST_APPROACH?.[fieldPath] ?? data?.COST_APPROACH?.[label] ?? data?.[fieldPath] ?? data?.[label] ?? '';
    const valStr = renderValue(val);
    const targetPath = ['COST_APPROACH', fieldPath];

    return (
      <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '120px', whiteSpace: 'nowrap' }}>{label}</span>
          <div style={{ flexGrow: 1 }}>
            <EditableField
              fieldPath={targetPath}
              value={valStr}
              onDataChange={onDataChange}
              editingField={editingField}
              setEditingField={setEditingField}
              isMissing={false}
              isEditable={true}
              allData={allData}
              manualValidations={manualValidations}
              handleManualValidation={handleManualValidation}
              revisionHandlers={revisionHandlers}
              inputClassName="form-control form-control-sm field-value"
              inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
            />
          </div>
        </div>
      </div>
    );
  };

  const getImpValue = (keys) => {
    const keyList = Array.isArray(keys) ? keys : [keys];
    for (const key of keyList) {
      const val = data?.IMPROVEMENTS?.[key] ?? data?.[key];
      if (val !== undefined && val !== null && String(val).trim() !== '') {
        return { value: val, actualKey: key };
      }
    }
    return { value: '', actualKey: keyList[0] };
  };

  const getFieldPath = (actualKey) => {
    if (data?.IMPROVEMENTS && actualKey in data.IMPROVEMENTS) {
      return ['IMPROVEMENTS', actualKey];
    }
    if (data && actualKey in data) {
      return [actualKey];
    }
    return ['IMPROVEMENTS', actualKey];
  };

  const checkOptionMatches = (valStr, opt) => {
    if (!valStr || !opt) return false;
    const v = String(valStr).trim().toLowerCase();
    const optLower = opt.trim().toLowerCase();
    const o = optLower.replace(/\./g, '');

    // Handle Units special case: "One" should NOT match "One with Accessory Unit"
    if (opt === 'One') {
      return v === 'one' || (/\bone\b/i.test(v) && !v.includes('accessory'));
    }
    if (opt === 'One with Accessory Unit') {
      return v.includes('accessory');
    }

    // Exact string match
    if (v === optLower || v === o) return true;

    // Split by commas, slashes, or semicolons
    const tokens = v.split(/[,;/]+/).map(t => t.trim()).filter(Boolean);
    for (const token of tokens) {
      const t = token.toLowerCase();
      const tClean = t.replace(/\./g, '').trim();

      if (t === optLower || tClean === o) return true;
      if (o === 'det' && (tClean === 'detached' || tClean === 'det')) return true;
      if (o === 'att' && (tClean === 'attached' || tClean === 'att')) return true;
      if ((o.includes('s-det') || o.includes('end unit')) && (tClean.includes('semi') || tClean.includes('s-det') || tClean.includes('end unit'))) return true;
      if (o === 'existing' && tClean === 'existing') return true;
      if (o === 'proposed' && tClean === 'proposed') return true;
      if (o.includes('under') && tClean.includes('under')) return true;
      if (o === 'concrete slab' && (tClean.includes('slab') || tClean === 'concrete slab')) return true;
      if (o === 'crawl space' && (tClean.includes('crawl') || tClean === 'crawl space')) return true;
      if (o === 'full basement' && (tClean.includes('full') || tClean === 'full basement')) return true;
      if (o === 'partial basement' && (tClean.includes('partial') || tClean === 'partial basement')) return true;
      if (o.includes('outside') && (tClean.includes('outside') || tClean.includes('entry'))) return true;
      if (o.includes('sump') && (tClean.includes('sump') || tClean.includes('pump'))) return true;
      if (o === 'none' && tClean === 'none') return true;
      if (o.includes('refrigerator') && tClean.includes('refrigerator')) return true;
      if (o.includes('range') && (tClean.includes('range') || tClean.includes('oven'))) return true;
      if (o.includes('dishwasher') && tClean.includes('dishwasher')) return true;
      if (o.includes('disposal') && tClean.includes('disposal')) return true;
      if (o.includes('microwave') && tClean.includes('microwave')) return true;
      if (o.includes('washer') && (tClean.includes('washer') || tClean.includes('dryer'))) return true;
      if (o.includes('fwa') && tClean === 'fwa') return true;
      if (o.includes('hwbb') && tClean === 'hwbb') return true;
      if (o.includes('radiant') && tClean === 'radiant') return true;
      if (o.includes('central') && (tClean.includes('central') || tClean.includes('central air'))) return true;
      if (o.includes('woodstove') && tClean.includes('woodstove')) return true;
      if (o.includes('fireplace') && tClean.includes('fireplace')) return true;
      if (o.includes('fence') && tClean.includes('fence')) return true;
      if (o.includes('patio') && (tClean.includes('patio') || tClean.includes('deck'))) return true;
      if (o.includes('porch') && tClean.includes('porch')) return true;
      if (o.includes('pool') && tClean.includes('pool')) return true;
      if (o === 'driveway' && (tClean.includes('driveway') || tClean === 'driveway')) return true;
      if (o === 'garage' && (tClean.includes('garage') || tClean === 'garage')) return true;
      if (o === 'carport' && (tClean.includes('carport') || tClean === 'carport')) return true;
    }
    return false;
  };

  const renderImpField = (label, keys, options = []) => {
    const { value: rawVal, actualKey } = getImpValue(keys);
    const valStr = renderValue(rawVal);
    const targetPath = getFieldPath(actualKey);

    return (
      <div style={{ borderBottom: '1px solid #e9ecef', paddingBottom: '3px', marginBottom: '4px' }}>
        <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', marginBottom: '2px' }}>
          {label}
        </div>
        {options.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 8px', marginBottom: '3px' }}>
            {options.map(opt => {
              const isChecked = checkOptionMatches(valStr, opt);
              const handleToggle = () => {
                let items = valStr ? valStr.split(',').map(s => s.trim()).filter(Boolean) : [];
                if (isChecked) {
                  items = items.filter(item => !checkOptionMatches(item, opt));
                } else {
                  items.push(opt);
                }
                const newVal = items.join(', ');
                onDataChange(targetPath, newVal);
              };
              return (
                <label key={opt} style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', cursor: 'pointer', fontSize: '0.7rem', userSelect: 'none', margin: 0 }}>
                  <input type="checkbox" checked={isChecked} onChange={handleToggle} style={{ margin: 0, width: '12px', height: '12px' }} />
                  <span>{opt}</span>
                </label>
              );
            })}
          </div>
        )}
        <EditableField
          fieldPath={targetPath}
          value={valStr}
          onDataChange={onDataChange}
          editingField={editingField}
          setEditingField={setEditingField}
          isEditable={true}
          allData={allData}
          manualValidations={manualValidations}
          handleManualValidation={handleManualValidation}
          revisionHandlers={revisionHandlers}
          inputClassName="form-control form-control-sm field-value"
          inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.75rem', height: 'auto' }}
        />
      </div>
    );
  };

  const renderImpNarrativeField = (keys) => {
    const { value: rawVal, actualKey } = getImpValue(keys);
    const valStr = renderValue(rawVal);
    const targetPath = getFieldPath(actualKey);
    return (
      <EditableField
        fieldPath={targetPath}
        value={valStr}
        onDataChange={onDataChange}
        editingField={editingField}
        setEditingField={setEditingField}
        usePre={true}
        isEditable={true}
        allData={allData}
        manualValidations={manualValidations}
        handleManualValidation={handleManualValidation}
        revisionHandlers={revisionHandlers}
        inputClassName="form-control form-control-sm field-value-pre"
        inputStyle={{ width: '100%', border: '1px solid #ced4da', background: '#fff', padding: '4px', fontSize: '0.8rem', height: 'auto', minHeight: '40px', resize: 'vertical' }}
      />
    );
  };

  if (id === 'improvements-section') {
    return (
      <Paper id={id} elevation={1} sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', borderTop: '3px solid', borderTopColor: borderColor }}>
        <Box
          sx={{
            p: 1.5,
            bgcolor: 'grey.50',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'grey.200',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
          <Typography variant="h6" component="h5" sx={{ fontSize: '1.05rem', fontWeight: 'bold' }}>{title || "Improvements Section"}</Typography>
          {onRevisionButtonClick && (
            <Tooltip title="Revision Language">
              <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'text.secondary', ml: 'auto' }}><LibraryBooksIcon /></IconButton>
            </Tooltip>
          )}
        </Box>
        {loading && loadingSection === id && (
          <Box sx={{ width: '100%' }}><LinearProgress /></Box>
        )}
        <div className="card-body p-2" style={{ fontSize: '0.78rem', backgroundColor: '#fff', overflowX: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(220px, 1fr))', gap: '8px', border: '1px solid #ced4da', borderRadius: '4px', padding: '4px' }}>
            
            {/* COLUMN 1: GENERAL DESCRIPTION */}
            <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ backgroundColor: '#e9ecef', padding: '4px 8px', fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center', borderBottom: '1px solid #dee2e6' }}>
                GENERAL DESCRIPTION
              </div>
              <div style={{ padding: '4px' }}>
                {renderImpField("Units", ["Units", "One with Accessory Unit"], ["One", "One with Accessory Unit"])}
                {renderImpField("# of Stories", ["# of Stories"])}
                {renderImpField("Type", ["Type", "Property Type"], ["Det.", "Att.", "S-Det./End Unit"])}
                {renderImpField("Status", ["Existing/Proposed/Under Const.", "Construction Status"], ["Existing", "Proposed", "Under Const."])}
                {renderImpField("Design (Style)", ["Design (Style)", "Design Style"])}
                {renderImpField("Year Built", ["Year Built"])}
                {renderImpField("Effective Age (Yrs)", ["Effective Age (Yrs)", "Effective Age"])}
                {renderImpField("Attic", ["Attic"], ["None", "Drop Stair", "Stairs", "Floor", "Scuttle", "Finished", "Heated"])}
                {renderImpField("Appliances", ["Appliances"], ["Refrigerator", "Range/Oven", "Dishwasher", "Disposal", "Microwave", "Washer/Dryer"])}
              </div>
            </div>

            {/* COLUMN 2: FOUNDATION */}
            <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ backgroundColor: '#e9ecef', padding: '4px 8px', fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center', borderBottom: '1px solid #dee2e6' }}>
                FOUNDATION
              </div>
              <div style={{ padding: '4px' }}>
                {renderImpField("Foundation", ["Foundation Type", "Foundation"], ["Concrete Slab", "Crawl Space", "Full Basement", "Partial Basement"])}
                {renderImpField("Basement Area", ["Basement Area sq.ft.", "Basement Area"])}
                {renderImpField("Basement Finish", ["Basement Finish %", "Basement Finish"])}
                {renderImpField("Details", ["Basement Details"], ["Outside Entry/Exit", "Sump Pump"])}
                {renderImpField("Evidence of", ["Evidence of (Foundation)", "Evidence of"], ["Infestation", "Dampness", "Settlement", "None"])}
                {renderImpField("Heating", ["Heating Type"], ["FWA", "HWBB", "Radiant", "Other"])}
                {renderImpField("Fuel", ["Fuel", "Heating Fuel"])}
                {renderImpField("Cooling", ["Cooling Type"], ["Central Air Conditioning", "Individual", "Other"])}
              </div>
            </div>

            {/* COLUMN 3: EXTERIOR DESCRIPTION */}
            <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ backgroundColor: '#e9ecef', padding: '4px 8px', fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center', borderBottom: '1px solid #dee2e6' }}>
                EXTERIOR DESCRIPTION <span style={{ fontWeight: 'normal', fontSize: '0.65rem' }}>materials/condition</span>
              </div>
              <div style={{ padding: '4px' }}>
                {renderImpField("Foundation Walls", ["Foundation Walls (Material/Condition)", "Foundation Walls"])}
                {renderImpField("Exterior Walls", ["Exterior Walls (Material/Condition)", "Exterior Walls"])}
                {renderImpField("Roof Surface", ["Roof Surface (Material/Condition)", "Roof Surface"])}
                {renderImpField("Gutters & Downspouts", ["Gutters & Downspouts (Material/Condition)", "Gutters & Downspouts"])}
                {renderImpField("Window Type", ["Window Type (Material/Condition)", "Window Type"])}
                {renderImpField("Storm Sash/Insulated", ["Storm Sash/Insulated"])}
                {renderImpField("Screens", ["Screens"])}
                {renderImpField("Amenities", ["Amenities", "Patio/Deck", "Fence", "Porch", "Pool"], ["WoodStove", "Fireplace", "Fence", "Patio/Deck", "Porch", "Pool"])}
              </div>
            </div>

            {/* COLUMN 4: INTERIOR */}
            <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ backgroundColor: '#e9ecef', padding: '4px 8px', fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center', borderBottom: '1px solid #dee2e6' }}>
                INTERIOR <span style={{ fontWeight: 'normal', fontSize: '0.65rem' }}>materials/condition</span>
              </div>
              <div style={{ padding: '4px' }}>
                {renderImpField("Floors", ["Floors (Material/Condition)", "Floors"])}
                {renderImpField("Walls", ["Walls (Material/Condition)", "Walls"])}
                {renderImpField("Trim/Finish", ["Trim/Finish (Material/Condition)", "Trim/Finish"])}
                {renderImpField("Bath Floor", ["Bath Floor (Material/Condition)", "Bath Floor"])}
                {renderImpField("Bath Wainscot", ["Bath Wainscot (Material/Condition)", "Bath Wainscot"])}
                {renderImpField("Car Storage", ["Car Storage"], ["None", "Driveway", "Garage", "Carport", "Att.", "Det.", "Built-in"])}
                {renderImpField("# of Cars", ["Driveway # of Cars", "# of Cars"])}
                {renderImpField("Driveway Surface", ["Driveway Surface"])}
              </div>
            </div>

          </div>

          {/* SUMMARY COMMENTS AT BOTTOM */}
          <div style={{ marginTop: '12px', borderTop: '1px dashed #dee2e6', paddingTop: '8px' }}>
            <div style={{ marginBottom: '8px' }}>
              <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '2px' }}>
                Describe the condition of the property (including needed repairs, deterioration, renovations, remodeling, etc.):
              </div>
              {renderImpNarrativeField(["Describe the condition of the property", "Describe the condition of the property (including needed repairs, deterioration, renovations, remodeling, etc.)"])}
            </div>
            <div style={{ marginBottom: '8px' }}>
              <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '2px' }}>
                Are there any physical deficiencies or adverse conditions that affect the livability, soundness, or structural integrity of the property? If Yes, describe:
              </div>
              {renderImpNarrativeField(["Are there any physical deficiencies or adverse conditions that affect the livability, soundness, or structural integrity of the property? If Yes, describe", "Are there any physical deficiencies or adverse conditions that affect the livability, soundness, or structural integrity of the property?"])}
            </div>
            <div>
              <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '2px' }}>
                Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)? If No, describe:
              </div>
              {renderImpNarrativeField(["Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)?", "Does the property generally conform to the neighborhood (functional utility, style, condition, use, construction, etc.)? If No, describe"])}
            </div>
          </div>
        </div>
      </Paper>
    );
  }

  if (id === 'cost-approach-section') {
    const costData = data?.COST_APPROACH || data || {};
    return (
      <Paper id={id} elevation={1} sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', borderTop: '3px solid', borderTopColor: borderColor }}>
        <Box
          sx={{
            p: 1.5,
            bgcolor: 'grey.50',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'grey.200',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
          <Typography variant="h6" component="h5" sx={{ fontSize: '1.05rem', fontWeight: 'bold' }}>{title || "Cost Approach"}</Typography>
          {onRevisionButtonClick && (
            <Tooltip title="Revision Language">
              <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'text.secondary', ml: 'auto' }}><LibraryBooksIcon /></IconButton>
            </Tooltip>
          )}
        </Box>
        {loading && loadingSection === id && (
          <Box sx={{ width: '100%' }}><LinearProgress /></Box>
        )}
        <div className="card-body p-3" style={{ fontSize: '0.8rem', backgroundColor: '#fff' }}>

          <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '12px', marginBottom: '16px' }}>
            <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '4px' }}>
              Provide adequate information for the lender/client to replicate the below cost figures and calculations.
            </div>
            <div style={{ minHeight: '40px', marginBottom: '12px' }}>
              <EditableField
                fieldPath={["COST_APPROACH", "Provide adequate information for the lender/client to replicate the below cost figures and calculations."]}
                value={renderValue(costData["Provide adequate information for the lender/client to replicate the below cost figures and calculations."] || '')}
                onDataChange={onDataChange}
                editingField={editingField}
                setEditingField={setEditingField}
                usePre={true}
                isMissing={false}
                isEditable={true}
                allData={allData}
                manualValidations={manualValidations}
                handleManualValidation={handleManualValidation}
                revisionHandlers={revisionHandlers}
                inputClassName="form-control form-control-sm field-value-pre"
                inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto', minHeight: '40px', resize: 'vertical' }}
              />
            </div>

            <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '4px' }}>
              Support for the opinion of site value (summary of comparable land sales or other methods for estimating site value)
            </div>
            <div style={{ minHeight: '40px' }}>
              <EditableField
                fieldPath={["COST_APPROACH", "Support for the opinion of site value (summary of comparable land sales or other methods for estimating site value)"]}
                value={renderValue(costData["Support for the opinion of site value (summary of comparable land sales or other methods for estimating site value)"] || '')}
                onDataChange={onDataChange}
                editingField={editingField}
                setEditingField={setEditingField}
                usePre={true}
                isMissing={false}
                isEditable={true}
                allData={allData}
                manualValidations={manualValidations}
                handleManualValidation={handleManualValidation}
                revisionHandlers={revisionHandlers}
                inputClassName="form-control form-control-sm field-value-pre"
                inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto', minHeight: '40px', resize: 'vertical' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '24px' }}>
            <div style={{ flex: 1, minWidth: 0, borderRight: '1px solid #dee2e6', paddingRight: '16px' }}>
              <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '12px', borderBottom: '2px solid #343a40', paddingBottom: '4px' }}>
                SUPPORT & DETAILS
              </div>

              {renderCostField("ESTIMATED COST NEW TYPE", "Estimated")}
              {renderCostField("Source of Cost Data", "Source of cost data")}

              <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '80px', whiteSpace: 'nowrap' }}>Quality Rating</span>
                  <div style={{ flexGrow: 1 }}>
                    <EditableField
                      fieldPath={["COST_APPROACH", "Quality rating from cost service "]}
                      value={renderValue(costData["Quality rating from cost service "] || costData["Quality rating from cost service"] || costData["Quality Rating"] || '')}
                      onDataChange={onDataChange}
                      editingField={editingField}
                      setEditingField={setEditingField}
                      isEditable={true}
                      allData={allData}
                      manualValidations={manualValidations}
                      handleManualValidation={handleManualValidation}
                      revisionHandlers={revisionHandlers}
                      inputClassName="form-control form-control-sm field-value"
                      inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                    />
                  </div>
                  <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', whiteSpace: 'nowrap' }}>Effective Date</span>
                  <div style={{ width: '80px' }}>
                    <EditableField
                      fieldPath={["COST_APPROACH", "Effective date of cost data "]}
                      value={renderValue(costData["Effective date of cost data "] || costData["Effective date of cost data"] || costData["Effective Date"] || '')}
                      onDataChange={onDataChange}
                      editingField={editingField}
                      setEditingField={setEditingField}
                      isEditable={true}
                      allData={allData}
                      manualValidations={manualValidations}
                      handleManualValidation={handleManualValidation}
                      revisionHandlers={revisionHandlers}
                      inputClassName="form-control form-control-sm field-value"
                      inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', marginBottom: '4px' }}>
                  Comments on Cost Approach (gross living area calculations, depreciation, etc.)
                </div>
                <div style={{ minHeight: '60px', marginTop: '4px' }}>
                  <EditableField
                    fieldPath={["COST_APPROACH", "Comments on Cost Approach (gross living area calculations, depreciation, etc.)"]}
                    value={renderValue(costData["Comments on Cost Approach (gross living area calculations, depreciation, etc.)"] || '')}
                    onDataChange={onDataChange}
                    editingField={editingField}
                    setEditingField={setEditingField}
                    usePre={true}
                    isMissing={false}
                    isEditable={true}
                    allData={allData}
                    manualValidations={manualValidations}
                    handleManualValidation={handleManualValidation}
                    revisionHandlers={revisionHandlers}
                    inputClassName="form-control form-control-sm field-value-pre"
                    inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto', minHeight: '60px', resize: 'vertical' }}
                  />
                </div>
              </div>

              {renderCostField("Remaining Economic Life", "Estimated Remaining Economic Life (HUD and VA only)")}
            </div>

            <div style={{ flex: 1, minWidth: 0, paddingLeft: '16px' }}>
              <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '12px', borderBottom: '2px solid #343a40', paddingBottom: '4px' }}>
                COST CALCULATIONS
              </div>

              {renderCostField("OPINION OF SITE VALUE", "OPINION OF SITE VALUE = $ ................................................")}
              {renderCostField("DWELLING", "Dwelling")}
              {renderCostField("Basement", "Basement")}
              {renderCostField("Deck", "Deck")}
              {renderCostField("Garage/Carport", "Garage/Carport ")}
              {renderCostField("Total Estimate Cost-New", "Total Estimate of Cost-New = $ ...................")}

              <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                <div style={{ fontWeight: 'bold', color: '#6c757d', fontSize: '0.65rem', marginBottom: '2px' }}>
                  Less: Physical | Functional | External
                </div>
                {renderCostField("Depreciation", "Depreciation ")}
              </div>

              {renderCostField("Depreciated Cost of Improvements", "Depreciated Cost of Improvements......................................................=$ ")}
              {renderCostField("As-is Value Site Improvements", "“As-is” Value of Site Improvements......................................................=$")}

              <div style={{ marginTop: '12px', backgroundColor: '#e9ecef', padding: '6px', borderRadius: '4px' }}>
                {renderCostField("INDICATED VALUE BY COST APPROACH", "Indicated Value By Cost Approach......................................................=$")}
              </div>
            </div>
          </div>

        </div>
      </Paper>
    );
  }

  if (id === 'income-approach-section') {
    const incData = data?.INCOME_APPROACH || data || {};
    const rentVal = renderValue(incData["Estimated Monthly Market Rent $"] || incData["Estimated Monthly Market Rent"] || data?.["Estimated Monthly Market Rent $"] || '');
    const grmVal = renderValue(incData["X Gross Rent Multiplier  = $"] || incData["X Gross Rent Multiplier = $"] || incData["Gross Rent Multiplier"] || incData["X GROSS RENT MULTIPLIER = $"] || data?.["X Gross Rent Multiplier  = $"] || '');
    const indIncVal = renderValue(incData["Indicated Value by Income Approach"] || incData["Indicated Value by Income Approach $"] || incData["INDICATED VALUE BY INCOME APPROACH"] || data?.["Indicated Value by Income Approach"] || '');
    const sumVal = renderValue(incData["Summary of Income Approach (including support for market rent and GRM) "] || incData["Summary of Income Approach (including support for market rent and GRM)"] || incData["SUMMARY OF INCOME APPROACH"] || data?.["Summary of Income Approach (including support for market rent and GRM) "] || '');

    return (
      <Paper id={id} elevation={1} sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', borderTop: '3px solid', borderTopColor: borderColor }}>
        <Box
          sx={{
            p: 1.5,
            bgcolor: 'grey.50',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'grey.200',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
          <Typography variant="h6" component="h5" sx={{ fontSize: '1.05rem', fontWeight: 'bold' }}>{title || "Income Approach"}</Typography>
          {onRevisionButtonClick && (
            <Tooltip title="Revision Language">
              <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'text.secondary', ml: 'auto' }}><LibraryBooksIcon /></IconButton>
            </Tooltip>
          )}
        </Box>
        {loading && loadingSection === id && (
          <Box sx={{ width: '100%' }}><LinearProgress /></Box>
        )}
        <div className="card-body p-3" style={{ fontSize: '0.8rem', backgroundColor: '#fff' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px', borderBottom: '1px solid #dee2e6', paddingBottom: '12px' }}>
            <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px' }}>
              <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', display: 'block', marginBottom: '2px' }}>Estimated Monthly Market Rent $</span>
              <EditableField
                fieldPath={["INCOME_APPROACH", "Estimated Monthly Market Rent $"]}
                value={rentVal}
                onDataChange={onDataChange}
                editingField={editingField}
                setEditingField={setEditingField}
                isEditable={true}
                allData={allData}
                manualValidations={manualValidations}
                handleManualValidation={handleManualValidation}
                revisionHandlers={revisionHandlers}
                inputClassName="form-control form-control-sm field-value"
                inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
              />
            </div>
            <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px' }}>
              <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', display: 'block', marginBottom: '2px' }}>X Gross Rent Multiplier = $</span>
              <EditableField
                fieldPath={["INCOME_APPROACH", "X Gross Rent Multiplier  = $"]}
                value={grmVal}
                onDataChange={onDataChange}
                editingField={editingField}
                setEditingField={setEditingField}
                isEditable={true}
                allData={allData}
                manualValidations={manualValidations}
                handleManualValidation={handleManualValidation}
                revisionHandlers={revisionHandlers}
                inputClassName="form-control form-control-sm field-value"
                inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
              />
            </div>
            <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', backgroundColor: '#e9ecef', padding: '6px', borderRadius: '4px' }}>
              <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', display: 'block', marginBottom: '2px' }}>Indicated Value by Income Approach</span>
              <EditableField
                fieldPath={["INCOME_APPROACH", "Indicated Value by Income Approach"]}
                value={indIncVal}
                onDataChange={onDataChange}
                editingField={editingField}
                setEditingField={setEditingField}
                isEditable={true}
                allData={allData}
                manualValidations={manualValidations}
                handleManualValidation={handleManualValidation}
                revisionHandlers={revisionHandlers}
                inputClassName="form-control form-control-sm field-value"
                inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
              />
            </div>
          </div>

          <div>
            <div style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.75rem', marginBottom: '4px' }}>
              Summary of Income Approach (including support for market rent and GRM)
            </div>
            <EditableField
              fieldPath={["INCOME_APPROACH", "Summary of Income Approach (including support for market rent and GRM) "]}
              value={sumVal}
              onDataChange={onDataChange}
              editingField={editingField}
              setEditingField={setEditingField}
              usePre={true}
              isMissing={false}
              isEditable={true}
              allData={allData}
              manualValidations={manualValidations}
              handleManualValidation={handleManualValidation}
              revisionHandlers={revisionHandlers}
              inputClassName="form-control form-control-sm field-value-pre"
              inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto', minHeight: '60px', resize: 'vertical' }}
            />
          </div>
        </div>
      </Paper>
    );
  }

  if (id === 'appraiser-section') {
    const hasSupervisoryData = data && Object.keys(data).some(k => k.toLowerCase().includes('supervisory') && data[k] !== undefined && data[k] !== null && String(data[k]).trim() !== '');
    const hasAppraisedValue = data && data["APPRAISED VALUE OF SUBJECT PROPERTY $"] && String(data["APPRAISED VALUE OF SUBJECT PROPERTY $"]).trim() !== '';
    const hasSubjectInspection = data && (data["Did not inspect subject property"] === 'Yes' || data["Did inspect exterior of subject property from street"] === 'Yes' || data["Did inspect interior and exterior of subject property"] === 'Yes');
    const hasCompInspection = data && (data["Did not inspect exterior of comparable sales from street"] === 'Yes' || data["Did inspect exterior of comparable sales from street"] === 'Yes');
    const hasLenderData = data && (data["LENDER/CLIENT Name"] || data["Lender/Client Company Name"] || data["Lender/Client Company Address"] || data["Lender/Client Email Address"]);

    return (
      <Paper id={id} elevation={1} sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', borderTop: '3px solid', borderTopColor: borderColor }}>
        <Box
          sx={{
            p: 1.5,
            bgcolor: 'grey.50',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'grey.200',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
          <Typography variant="h6" component="h5" sx={{ fontSize: '1.05rem', fontWeight: 'bold' }}>{title}</Typography>
          {onRevisionButtonClick && (
            <Tooltip title="Revision Language">
              <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'text.secondary', ml: 'auto' }}><LibraryBooksIcon /></IconButton>
            </Tooltip>
          )}
        </Box>
        {loading && loadingSection === id && (
          <Box sx={{ width: '100%' }}><LinearProgress /></Box>
        )}
        <div className="card-body p-3" style={{ fontSize: '0.8rem', backgroundColor: '#fff' }}>

          <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '12px', borderBottom: '2px solid #343a40', paddingBottom: '4px' }}>
                APPRAISER
              </div>
              {data && data["Signature"] && String(data["Signature"]).trim() !== '' && (
                <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '100px', whiteSpace: 'nowrap' }}>Signature</span>
                    <div style={{ flexGrow: 1 }}>
                      <EditableField
                        fieldPath={["Signature"]}
                        value={data ? renderValue(data["Signature"]) : ''}
                        onDataChange={onDataChange}
                        editingField={editingField}
                        setEditingField={setEditingField}
                        isEditable={true}
                        allData={allData}
                        manualValidations={manualValidations}
                        handleManualValidation={handleManualValidation}
                        revisionHandlers={revisionHandlers}
                        inputClassName="form-control form-control-sm field-value"
                        inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                        valueStyle={{ fontFamily: "'Caveat', 'Dancing Script', 'Brush Script MT', cursive, sans-serif", fontSize: '1.25rem', color: '#1a252c', fontStyle: 'italic' }}
                      />
                    </div>
                  </div>
                </div>
              )}
              {renderCertField("Name", "Name")}
              {renderCertField("Company Name", "Company Name")}
              {renderCertField("Company Address", "Company Address")}
              {renderCertField("Telephone Number", "Telephone Number")}
              {renderCertField("Email Address", "Email Address")}
              {renderCertField("Date of Signature", "Date of Signature and Report")}
              {renderCertField("Effective Date of Appraisal", "Effective Date of Appraisal")}
              {renderCertField("State Certification #", "State Certification #")}
              {renderCertField("or State License #", "or State License #")}


              {(!hideEmptyFields || (data && (data["or Other (describe)"] || data["State #"]))) && (
                <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '100px', whiteSpace: 'nowrap' }}>or Other (describe)</span>
                    <div style={{ flexGrow: 1 }}>
                      <EditableField
                        fieldPath={["or Other (describe)"]}
                        value={data ? renderValue(data["or Other (describe)"]) : ''}
                        onDataChange={onDataChange}
                        editingField={editingField}
                        setEditingField={setEditingField}
                        isEditable={true}
                        allData={allData}
                        manualValidations={manualValidations}
                        handleManualValidation={handleManualValidation}
                        revisionHandlers={revisionHandlers}
                        inputClassName="form-control form-control-sm field-value"
                        inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                      />
                    </div>
                    <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem' }}>State #</span>
                    <div style={{ width: '80px' }}>
                      <EditableField
                        fieldPath={["State #"]}
                        value={data ? renderValue(data["State #"]) : ''}
                        onDataChange={onDataChange}
                        editingField={editingField}
                        setEditingField={setEditingField}
                        isEditable={true}
                        allData={allData}
                        manualValidations={manualValidations}
                        handleManualValidation={handleManualValidation}
                        revisionHandlers={revisionHandlers}
                        inputClassName="form-control form-control-sm field-value"
                        inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {renderCertField("State", "State")}
              {renderCertField("Expiration Date", "Expiration Date of Certification or License")}
            </div>

            {/* Right: SUPERVISORY APPRAISER */}
            {(!hideEmptyFields || hasSupervisoryData) && (
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '12px', borderBottom: '2px solid #343a40', paddingBottom: '4px' }}>
                  SUPERVISORY APPRAISER (ONLY IF REQUIRED)
                </div>
                {(!hideEmptyFields || (data && data["Supervisory Signature"])) && (
                  <div style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '3px', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                      <span style={{ fontWeight: 'bold', color: '#495057', fontSize: '0.7rem', minWidth: '100px', whiteSpace: 'nowrap' }}>Signature</span>
                      <div style={{ flexGrow: 1 }}>
                        <EditableField
                          fieldPath={["Supervisory Signature"]}
                          value={data ? renderValue(data["Supervisory Signature"]) : ''}
                          onDataChange={onDataChange}
                          editingField={editingField}
                          setEditingField={setEditingField}
                          isEditable={true}
                          allData={allData}
                          manualValidations={manualValidations}
                          handleManualValidation={handleManualValidation}
                          revisionHandlers={revisionHandlers}
                          inputClassName="form-control form-control-sm field-value"
                          inputStyle={{ width: '100%', border: 'none', background: 'transparent', padding: 0, fontSize: '0.8rem', height: 'auto' }}
                          valueStyle={{ fontFamily: "'Caveat', 'Dancing Script', 'Brush Script MT', cursive, sans-serif", fontSize: '1.25rem', color: '#1a252c', fontStyle: 'italic' }}
                        />
                      </div>
                    </div>
                  </div>
                )}
                {renderCertField("Name", "Supervisory Name")}
                {renderCertField("Company Name", "Supervisory Company Name")}
                {renderCertField("Company Address", "Supervisory Company Address")}
                {renderCertField("Telephone Number", "Supervisory Telephone Number")}
                {renderCertField("Email Address", "Supervisory Email Address")}
                {renderCertField("Date of Signature", "Supervisory Date of Signature")}
                {renderCertField("State Certification #", "Supervisory State Certification #")}
                {renderCertField("or State License #", "Supervisory or State License #")}
                {renderCertField("State", "Supervisory State")}
                {renderCertField("Expiration Date", "Supervisory Expiration Date of Certification or License")}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '24px', borderTop: '2px solid #495057', paddingTop: '16px' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 'bold', fontSize: '0.8rem', marginBottom: '8px', color: '#343a40' }}>
                ADDRESS OF PROPERTY APPRAISED
              </div>
              {renderCertField("Address", "ADDRESS OF PROPERTY APPRAISED")}

              {(!hideEmptyFields || hasAppraisedValue) && (
                <>
                  <div style={{ fontWeight: 'bold', fontSize: '0.8rem', marginTop: '16px', marginBottom: '8px', color: '#343a40' }}>
                    APPRAISED VALUE OF SUBJECT PROPERTY
                  </div>
                  {renderCertField("Appraised Value $", "APPRAISED VALUE OF SUBJECT PROPERTY $")}
                </>
              )}

              {(!hideEmptyFields || hasLenderData) && (
                <>
                  <div style={{ fontWeight: 'bold', fontSize: '0.8rem', marginTop: '16px', marginBottom: '8px', color: '#343a40' }}>
                    LENDER/CLIENT
                  </div>
                  {renderCertField("Name", "LENDER/CLIENT Name")}
                  {renderCertField("Company Name", "Lender/Client Company Name")}
                  {renderCertField("Company Address", "Lender/Client Company Address")}
                  {renderCertField("Email Address", "Lender/Client Email Address")}
                </>
              )}
            </div>

            {(!hideEmptyFields || hasSubjectInspection || hasCompInspection) && (
              <div style={{ flex: 1, minWidth: 0 }}>
                {(!hideEmptyFields || hasSubjectInspection) && (
                  <>
                    <div style={{ fontWeight: 'bold', fontSize: '0.8rem', marginBottom: '8px', color: '#343a40' }}>
                      SUBJECT PROPERTY
                    </div>
                    {renderCertField("Did not inspect subject property", "Did not inspect subject property", true)}
                    {renderCertField("Did inspect exterior of subject property from street", "Did inspect exterior of subject property from street", true)}
                    <div style={{ paddingLeft: '24px' }}>
                      {renderCertField("Date of Inspection", "Subject Property Date of Inspection (Exterior)")}
                    </div>
                    {renderCertField("Did inspect interior and exterior of subject property", "Did inspect interior and exterior of subject property", true)}
                    <div style={{ paddingLeft: '24px' }}>
                      {renderCertField("Date of Inspection", "Subject Property Date of Inspection (Interior/Exterior)")}
                    </div>
                  </>
                )}

                {(!hideEmptyFields || hasCompInspection) && (
                  <>
                    <div style={{ fontWeight: 'bold', fontSize: '0.8rem', marginTop: '16px', marginBottom: '8px', color: '#343a40' }}>
                      COMPARABLE SALES
                    </div>
                    {renderCertField("Did not inspect exterior of comparable sales from street", "Did not inspect exterior of comparable sales from street", true)}
                    {renderCertField("Did inspect exterior of comparable sales from street", "Did inspect exterior of comparable sales from street", true)}
                    <div style={{ paddingLeft: '24px' }}>
                      {renderCertField("Date of Inspection", "Comparable Sales Date of Inspection")}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>


          <div style={{ borderTop: '1px dashed #dee2e6', marginTop: '20px', paddingTop: '12px' }}>
            <div style={{ fontWeight: 'bold', fontSize: '0.8rem', color: '#6c757d', marginBottom: '8px' }}>
              Additional Info & E&O Insurance
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {renderCertField("Appraiser License", "Appraiser License")}
              {renderCertField("E&O Insurance", "E&O Insurance")}
              {renderCertField("Policy Period From", "Policy Period From")}
              {renderCertField("Policy Period To", "Policy Period To")}
              {renderCertField("License Valid To", "License Valid To")}
              {renderCertField("License # / Reg #", "LICENSE/REGISTRATION/CERTIFICATION #")}
            </div>
          </div>

        </div>
      </Paper>
    );
  }

  return (
    <Paper id={id} elevation={1} sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', borderTop: '3px solid', borderTopColor: borderColor }}>
      <Box
        sx={{
          p: 1.5,
          bgcolor: 'grey.50',
          color: 'text.primary',
          borderBottom: '1px solid',
          borderColor: 'grey.200',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" component="h5" sx={{ fontSize: '1.05rem', fontWeight: 'bold' }}>{title}</Typography>
          {renderNeighborhoodTotal()}
        </Box>
        {onRevisionButtonClick && (
          <Tooltip title="Revision Language">
            <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'text.secondary', ml: 'auto' }}><LibraryBooksIcon /></IconButton>
          </Tooltip>
        )}
      </Box>
      {loading && loadingSection === id && (
        <Box sx={{ width: '100%' }}><LinearProgress /></Box>
      )}
      <div className="card-body subject-grid-container">
        {getDynamicFields().map(field => renderGridItem(field))}
      </div>
    </Paper>
  );
};
