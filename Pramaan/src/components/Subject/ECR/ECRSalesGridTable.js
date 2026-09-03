import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  IconButton
} from '@mui/material';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import { EditableField, GridInfoCard } from '../components/FormComponents';
import {
  ecrSalesGridAttributes,
  ecrSalesGridNarrativeFields,
  ecrComparableSalesList
} from './ecrFields';

export const ECRSalesGridTable = ({
  id = "sales-comparison-section",
  data = {},
  allData,
  extractionAttempted,
  handleDataChange,
  editingField,
  setEditingField,
  isEditable = true,
  manualValidations,
  handleManualValidation,
  onRevisionButtonClick,
  revisionHandlers
}) => {
  const comparableSales = ecrComparableSalesList;
  const gridData = data?.SALES_COMPARISON || data || {};

  return (
    <Box sx={{ mb: 2 }}>
      {/* 1. SALES COMPARISON GRID TABLE (Subject + Comps 1-6) */}
      <Paper
        id={id}
        elevation={2}
        sx={{
          mb: 1.5,
          borderRadius: 2,
          overflow: 'hidden',
          border: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            px: 2,
            py: 0.8,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 10
          }}
        >
          <Box>
            <Typography variant="subtitle2" fontWeight="bold">
              Sales Comparison Analysis Grid
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Subject Property & Comparable Sales #1 – #6
            </Typography>
          </Box>
          {onRevisionButtonClick && (
            <Tooltip title="Revision Language">
              <IconButton onClick={onRevisionButtonClick} size="small" sx={{ color: 'white', ml: 'auto', p: 0.5 }}>
                <LibraryBooksIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        <TableContainer sx={{ maxHeight: 750 }}>
          <Table size="small" stickyHeader aria-label="ECR sales comparison grid" sx={{ minWidth: 900 }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, minWidth: 200, bgcolor: 'grey.100', borderRight: '1px solid #e0e0e0' }}>
                  Feature / Grid Attribute
                </TableCell>
                <TableCell sx={{ fontWeight: 700, minWidth: 170, bgcolor: '#e3f2fd', borderRight: '1px solid #e0e0e0', color: 'primary.dark' }}>
                  Subject
                </TableCell>
                {comparableSales.map((sale, idx) => (
                  <TableCell
                    key={sale}
                    sx={{
                      fontWeight: 700,
                      minWidth: 170,
                      bgcolor: idx % 2 === 0 ? 'grey.50' : 'background.paper',
                      borderRight: '1px solid #e0e0e0'
                    }}
                  >
                    Comp #{idx + 1}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {ecrSalesGridAttributes.map((attr, idx) => {
                const isHighlight = attr === 'Sales Price' || attr === 'Adjusted Sales Price' || attr === 'Net Adjustment';

                return (
                  <TableRow
                    key={attr}
                    hover
                    sx={{
                      bgcolor: isHighlight ? 'rgba(25, 118, 210, 0.04)' : (idx % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.015)')
                    }}
                  >
                    {/* Feature Label */}
                    <TableCell
                      sx={{
                        fontWeight: isHighlight ? 700 : 500,
                        fontSize: '0.85rem',
                        borderRight: '1px solid #e0e0e0',
                        color: isHighlight ? 'primary.main' : 'text.primary'
                      }}
                    >
                      {attr}
                    </TableCell>

                    {/* Subject Column */}
                    <TableCell
                      sx={{
                        borderRight: '1px solid #e0e0e0',
                        bgcolor: isHighlight ? 'rgba(227, 242, 253, 0.5)' : 'inherit',
                        fontSize: '0.85rem'
                      }}
                    >
                      <EditableField
                        fieldPath={['SALES_COMPARISON', 'Subject', attr]}
                        value={gridData?.Subject?.[attr] || gridData?.[attr] || ''}
                        onDataChange={handleDataChange}
                        editingField={editingField}
                        setEditingField={setEditingField}
                        isEditable={isEditable}
                        allData={allData || data}
                        saleName="Subject"
                        manualValidations={manualValidations}
                        handleManualValidation={handleManualValidation}
                        revisionHandlers={revisionHandlers}
                      />
                    </TableCell>

                    {/* Comparable Sales Columns 1 to 6 */}
                    {comparableSales.map((sale) => {
                      const compData = gridData?.[sale] || {};
                      const compVal = compData[attr] || '';

                      return (
                        <TableCell
                          key={sale}
                          sx={{
                            borderRight: '1px solid #e0e0e0',
                            fontSize: '0.85rem'
                          }}
                        >
                          <EditableField
                            fieldPath={['SALES_COMPARISON', sale, attr]}
                            value={compVal}
                            onDataChange={handleDataChange}
                            editingField={editingField}
                            setEditingField={setEditingField}
                            isEditable={isEditable}
                            allData={allData || data}
                            saleName={sale}
                            manualValidations={manualValidations}
                            handleManualValidation={handleManualValidation}
                            revisionHandlers={revisionHandlers}
                          />
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* 2. COMPARABLE DISCUSSIONS & RECONCILIATION CARD */}
      <GridInfoCard
        id="sales-comparison-narratives"
        title="Comparable Discussions & Reconciliation"
        fields={ecrSalesGridNarrativeFields}
        data={gridData}
        cardClass="bg-primary"
        usePre={true}
        extractionAttempted={extractionAttempted}
        onDataChange={(field, value) => handleDataChange(['SALES_COMPARISON', ...field], value)}
        editingField={editingField}
        setEditingField={setEditingField}
        isEditable={isEditable}
        allData={allData}
        manualValidations={manualValidations}
        handleManualValidation={handleManualValidation}
        onRevisionButtonClick={onRevisionButtonClick}
        revisionHandlers={revisionHandlers}
        showBlankValidation={extractionAttempted}
      />
    </Box>
  );
};

export default ECRSalesGridTable;
