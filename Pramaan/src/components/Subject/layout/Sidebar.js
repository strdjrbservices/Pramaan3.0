import React from 'react';
import { Tooltip, IconButton, List, ListItem, ListItemButton, ListItemText, Box, CircularProgress, ListItemIcon, Typography } from '@mui/material';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { keyframes } from '@mui/system';
import LightModeIcon from '@mui/icons-material/LightMode';
import NightlightRoundIcon from '@mui/icons-material/NightlightRound';
import PremiumLogo from '../../auth/logo';

const bounce = keyframes`
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-8px); }
  60% { transform: translateY(-4px); }
`;

const Sidebar = ({ sections, isOpen, isLocked, onLockToggle, onMouseEnter, onMouseLeave, onSectionClick, onThemeToggle, currentTheme, activeSection, loading, loadingSection, extractedSections = new Set(), visibleSections = new Set(), onArrowClick }) => (
    <>
        {isOpen && (
            <Box
                onClick={onLockToggle}
                sx={{
                    display: { xs: 'block', md: 'none' },
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100vw',
                    height: '100vh',
                    backgroundColor: 'rgba(0, 0, 0, 0.4)',
                    backdropFilter: 'blur(3px)',
                    zIndex: 1100,
                    transition: 'opacity 0.3s ease',
                }}
            />
        )}

        {!isOpen && (
            <IconButton
                onClick={onLockToggle}
                sx={{
                    display: { xs: 'flex', md: 'none' },
                    position: 'fixed',
                    bottom: 24,
                    left: 24,
                    zIndex: 1090,
                    backgroundColor: currentTheme === 'dark' ? '#1e88e5' : '#005A9C',
                    color: '#ffffff',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
                    '&:hover': {
                        backgroundColor: currentTheme === 'dark' ? '#1565c0' : '#004070',
                    },
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                }}
            >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </IconButton>
        )}

        <div className={`sidebar ${isOpen ? 'open' : 'closed'}`} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
            <div className="sidebar-header">
                <Box className="sidebar-logo" sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: 40, height: 40 }}>
                    <PremiumLogo size={40} fullScreen={false} />
                </Box>
                <Typography variant="h6" className="sidebar-title" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    DJRB
                </Typography>
                <Tooltip title={isLocked ? "Unpin Sidebar" : "Pin Sidebar"} placement="right">
                    <IconButton onClick={onLockToggle} size="small" className="sidebar-toggle-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isLocked ? 'rotate(45deg)' : 'none', transition: 'transform 0.2s' }}>
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                            <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                    </IconButton>
                </Tooltip>
                <Tooltip title="Toggle Dark/Light Theme" placement="right">
                    <IconButton onClick={onThemeToggle} size="small" sx={{ color: 'var(--primary-color)', ml: 1 }}>
                        {currentTheme === 'dark' ? <LightModeIcon /> : <NightlightRoundIcon />}
                    </IconButton>
                </Tooltip>
            </div>
            <List dense>
                {sections.map((section) => (
                    <ListItem key={section.id} disablePadding>
                        <Tooltip title={!isOpen ? section.title : ""} placement="right" arrow>
                            <ListItemButton
                                component="a"
                                href={`#${section.id}`}
                                className="sidebar-link"
                                selected={activeSection === section.id}
                                onClick={(e) => { e.preventDefault(); onSectionClick(section); }}
                                disabled={loading}
                                sx={{
                                    '&.Mui-selected': {
                                        backgroundColor: 'info.main', // A nice sky blue
                                        color: 'info.contrastText',
                                        '&:hover': { backgroundColor: 'info.dark' },
                                        '& .MuiListItemIcon-root': { color: 'info.contrastText' },
                                    },
                                }}>
                                {section.icon && (
                                    <ListItemIcon>
                                        {section.icon}
                                    </ListItemIcon>
                                )}
                                <ListItemText primary={section.title} />
                                {loadingSection === section.id && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                                        <CircularProgress size={16} color="inherit" />
                                    </Box>
                                )}
                                {extractedSections.has(section.id) && !visibleSections.has(section.id) && loadingSection !== section.id && (
                                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); onArrowClick(section.id); }} sx={{ rotate: '270deg', animation: `${bounce} 2s infinite`, ml: 'auto' }}>
                                        <ArrowDownwardIcon fontSize="small" />
                                    </IconButton>
                                )}
                            </ListItemButton>
                        </Tooltip>
                    </ListItem>
                ))}
            </List>
            <div className="sidebar-footer">
                Appraisal Extractor
            </div>
        </div>
    </>
);

export default Sidebar;
