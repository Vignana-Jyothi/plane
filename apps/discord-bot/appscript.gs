/**
 * DISCORD BOT BACKEND - ENHANCED GOOGLE APPS SCRIPT
 * Product Management Powerhouse Edition
 * 
 * Features:
 * - Task management with metrics tracking
 * - Wing showcase automation
 * - Intelligent reminder system
 * - Simplified meeting attendance tracking
 * 
 * Instructions:
 * 1. Paste this into a new Google Apps Script project
 * 2. Update SPREADSHEET_ID below
 * 3. Deploy as Web App:
 *    - Click "Deploy" -> "New Deployment"
 *    - Select type: "Web App"
 *    - Execute as: "Me"
 *    - Who has access: "Anyone"
 * 4. Copy the deployment URL to your .env file as APPSCRIPT_URL
 */

// ============ CONFIGURATION ============
const DEFAULT_SPREADSHEET_ID = "1GCeoldTAcNVpNLPIpFgXd6fSS0OQQPaDEJ7sybCcK94"; 

// Configure the spreadsheet ID for each wing below. You can leave them as "PASTE_ID_HERE"
// if you want them to fallback to the default spreadsheet until you create them.
const WING_SPREADSHEETS = {
  "Vision": "14Sz-I9TgGqlZ6Bijvpgb8ZHFjFbMEnVQjG_kB1G14q4",
  "Ignition": "1U_7ZWJQE5p3xwCx8E2kHPVfSqiOtPZNgeyKnB0dJpoM",
  "Infra": "1q9iOBiKlEAHBii7mxB01DKhZ99y-FjDM-7HvwhcaKKY",
  "Echo": "1DvPGwMjje4tzIuRdq7ui7yTF2dsChgpZOmpPvjLsHKY",
  "Talent": "1xFLAytMyHHeRKncVqdjPAiV81bbEMidSPQepHgzW878",
  "Fuel": "14Rt4yckZdhYAVHjm7W65S89UXBJY7_bxZ12zcGAiySc"
};

// ============ HELPER FUNCTIONS FOR MULTIPLE SHEETS ============
function getAllSpreadsheetIds() {
  const ids = [DEFAULT_SPREADSHEET_ID];
  for (const key in WING_SPREADSHEETS) {
    const id = WING_SPREADSHEETS[key];
    if (id && id !== "PASTE_ID_HERE" && ids.indexOf(id) === -1) {
      ids.push(id);
    }
  }
  return ids;
}

function getTargetSpreadsheetId(sheetName, data) {
  let wingName = null;
  if (sheetName === 'Tasks') {
     if (Array.isArray(data) && data.length > 7) wingName = data[7];
  } else if (sheetName === 'Meetings') {
     if (Array.isArray(data) && data.length > 1) wingName = data[1];
  } else if (sheetName === 'VisionPlans') {
     if (Array.isArray(data) && data.length > 1) wingName = data[1];
     else if (data && data.wing) wingName = data.wing;
  } else if (data && data.wing) {
     wingName = data.wing;
  }
  
  if (wingName && WING_SPREADSHEETS[wingName] && WING_SPREADSHEETS[wingName] !== "PASTE_ID_HERE") {
     return WING_SPREADSHEETS[wingName];
  }
  return DEFAULT_SPREADSHEET_ID;
}

function getAllDataFromSheet(sheetName, wingName) {
  // Tasks, Meetings, DelayTracker, and ScoreBoards are spread across multiple wing spreadsheets
  const multiSheetTypes = ['Tasks', 'Meetings', 'DelayTracker', 'ScoreBoards'];
  let allIds = [DEFAULT_SPREADSHEET_ID];
  
  if (multiSheetTypes.includes(sheetName)) {
    if (wingName && WING_SPREADSHEETS[wingName] && WING_SPREADSHEETS[wingName] !== "PASTE_ID_HERE") {
      allIds = [WING_SPREADSHEETS[wingName]];
      // Also check default just in case some are there
      if (WING_SPREADSHEETS[wingName] !== DEFAULT_SPREADSHEET_ID) {
        allIds.push(DEFAULT_SPREADSHEET_ID);
      }
    } else {
      allIds = getAllSpreadsheetIds();
    }
  }
  
  const combinedData = [];
  let headers = null;
  
  for (const ssId of allIds) {
    try {
      const ss = SpreadsheetApp.openById(ssId);
      const worksheet = ss.getSheetByName(sheetName);
      if (worksheet) {
        const data = worksheet.getDataRange().getValues();
        if (data && data.length > 0) {
          if (!headers) {
            headers = data[0];
            combinedData.push(headers);
          }
          for (let i = 1; i < data.length; i++) {
            combinedData.push(data[i]);
          }
        }
      }
    } catch (e) {
      // Ignore inaccessible sheets
      Logger.log("Error reading SS " + ssId + ": " + e);
    }
  }
  return combinedData;
}
 

// ============ GET REQUEST HANDLER ============
/**
 * Handle GET requests - Fetch data from sheets
 */
/**
 * Handle GET requests - Fetch data from sheets
 */
function doGet(e) {
  try {
    const sheet = e.parameter.sheet;
    const wing = e.parameter.wing;
    if (!sheet) return errorResponse('Sheet parameter required');
    
    const combinedData = getAllDataFromSheet(sheet, wing);
    if (combinedData.length === 0) return errorResponse(`Sheet "${sheet}" not found or empty`);
    
    return jsonResponse(combinedData);
  } catch (error) {
    return errorResponse(error.toString());
  }
}

// ============ POST REQUEST HANDLER ============
/**
 * Handle POST requests - Add or update data
 */
function doPost(e) {
  try {
    const sheetName = e.parameter.sheet;
    if (!sheetName) return errorResponse('Sheet parameter required');
    
    const data = JSON.parse(e.postData.contents);
    
    // Route to specialized update handlers
    if (sheetName === 'TasksUpdate') {
      return handleTasksUpdate(data);
    }
    
    if (sheetName === 'WingShowcaseUpdate') {
      return handleWingShowcaseUpdate(data);
    }
    
    if (sheetName === 'MeetingsUpdate') {
      return handleMeetingsUpdate(data);
    }
    
    if (sheetName === 'ProcessDelaysAndScores') {
      return handleProcessDelays(data);
    }
    
    if (sheetName === 'ReminderChannelsUpdate') {
      return handleReminderChannelsUpdate(data);
    }
    
    // Standard append operation
    const targetSsId = getTargetSpreadsheetId(sheetName, data);
    const ss = SpreadsheetApp.openById(targetSsId);
    let worksheet = ss.getSheetByName(sheetName);
    
    // Auto-create sheet with headers if missing
    if (!worksheet) {
      worksheet = ss.insertSheet(sheetName);
      const headers = getHeadersForSheet(sheetName);
      if (headers.length > 0) {
        worksheet.appendRow(headers);
        formatHeaderRow(worksheet, headers.length);
      }
    }
    
    const headers = worksheet.getRange(1, 1, 1, worksheet.getLastColumn()).getValues()[0];
    
    // Convert data to row format
    let rowToAppend;
    if (Array.isArray(data)) {
      rowToAppend = data;
    } else {
      rowToAppend = headers.map(h => data[h] !== undefined ? data[h] : '');
    }
    
    worksheet.appendRow(rowToAppend);
    
    // Apply specialized formatting if needed
    if (sheetName === 'VisionPlans') {
      formatVisionPlansSheet(worksheet);
    }

    return jsonResponse({ success: true, sheet: sheetName });
    
  } catch (error) {
    return errorResponse(error.toString());
  }
}

// ============ SPECIALIZED UPDATE HANDLERS ============

/**
 * Handle task updates (status, progress, message_id, etc.)
 * Supports matching by task_id or message_id
 */
function handleTasksUpdate(data) {
  try {
    const allIds = getAllSpreadsheetIds();
    
    for (const ssId of allIds) {
      let ss;
      try { ss = SpreadsheetApp.openById(ssId); } catch(e) { continue; }
      const sheet = ss.getSheetByName('Tasks');
      if (!sheet) continue;
      
      const rows = sheet.getDataRange().getValues();
      if (rows.length === 0) continue;
      const headers = rows[0];
      
      const colIndices = {
        task_id: headers.indexOf('task_id'),
        message_id: headers.indexOf('message_id'),
        status: headers.indexOf('status'),
        updated_at: headers.indexOf('updated_at'),
        metric_current: headers.indexOf('metric_current'),
        reminder_sent: headers.indexOf('reminder_sent'),
        last_reminder_sent: headers.indexOf('last_reminder_sent'),
        showcase_message_id: headers.indexOf('showcase_message_id'),
        assignee: headers.indexOf('assignee'),
        parent_id: headers.indexOf('parent_id'),
        channel_id: headers.indexOf('channel_id')
      };
      
      if (colIndices.task_id === -1 || colIndices.status === -1) continue;
      
      for (let i = 1; i < rows.length; i++) {
        const matchTask = data.task_id && String(rows[i][colIndices.task_id]) === String(data.task_id);
        const matchMsg = data.message_id && String(rows[i][colIndices.message_id]) === String(data.message_id);
        
        if (matchTask || matchMsg) {
          if (data.status === 'Deleted') {
            sheet.deleteRow(i + 1);
            return jsonResponse({ success: true, updated: true, message: 'Row deleted' });
          }
          if (data.status && colIndices.status !== -1) sheet.getRange(i + 1, colIndices.status + 1).setValue(data.status);
          if (data.assignee && colIndices.assignee !== -1) sheet.getRange(i + 1, colIndices.assignee + 1).setValue(data.assignee);
          if (data.message_id && colIndices.message_id !== -1) sheet.getRange(i + 1, colIndices.message_id + 1).setValue(data.message_id);
          if (data.metric_current !== undefined && colIndices.metric_current !== -1) sheet.getRange(i + 1, colIndices.metric_current + 1).setValue(data.metric_current);
          if (data.reminder_sent !== undefined && colIndices.reminder_sent !== -1) sheet.getRange(i + 1, colIndices.reminder_sent + 1).setValue(data.reminder_sent);
          if ((data.last_reminder !== undefined || data.last_reminder_sent !== undefined) && colIndices.last_reminder_sent !== -1) {
            sheet.getRange(i + 1, colIndices.last_reminder_sent + 1).setValue(data.last_reminder || data.last_reminder_sent);
          }
          if (data.showcase_message_id !== undefined && colIndices.showcase_message_id !== -1) sheet.getRange(i + 1, colIndices.showcase_message_id + 1).setValue(data.showcase_message_id);
          if (data.parent_id !== undefined && colIndices.parent_id !== -1) sheet.getRange(i + 1, colIndices.parent_id + 1).setValue(data.parent_id);
          if (data.channel_id !== undefined && colIndices.channel_id !== -1) sheet.getRange(i + 1, colIndices.channel_id + 1).setValue(data.channel_id);
          if (colIndices.updated_at !== -1) sheet.getRange(i + 1, colIndices.updated_at + 1).setValue(new Date().toISOString());
          return jsonResponse({ success: true, updated: true, row: i + 1 });
        }
      }
    }
    return jsonResponse({ success: true, updated: false, message: 'No matching task found' });
  } catch (error) {
    return errorResponse(error.toString());
  }
}

/**
 * Handle wing showcase updates
 * Updates or creates wing showcase tracking entries
 */
function handleWingShowcaseUpdate(data) {
  try {
    const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
    let sheet = ss.getSheetByName('WingShowcase');
    
    // Create sheet if it doesn't exist
    if (!sheet) {
      sheet = ss.insertSheet('WingShowcase');
      const headers = getHeadersForSheet('WingShowcase');
      sheet.appendRow(headers);
      formatHeaderRow(sheet, headers.length);
    }
    
    const rows = sheet.getDataRange().getValues();
    const headers = rows[0];
    
    // Find wing row
    const wingCol = headers.indexOf('wing_name');
    if (wingCol === -1) return errorResponse('wing_name column not found');
    
    for (let i = 1; i < rows.length; i++) {
      if (String(rows[i][wingCol]) === String(data.wing)) {
        // Update existing row
        if (data.weekly_message_id) {
          const col = headers.indexOf('weekly_message_id');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.weekly_message_id);
        }
        
        if (data.monthly_message_id) {
          const col = headers.indexOf('monthly_message_id');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.monthly_message_id);
        }
        
        if (data.last_updated) {
          const col = headers.indexOf('last_updated');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.last_updated);
        }
        
        if (data.active_tasks_count !== undefined) {
          const col = headers.indexOf('active_tasks_count');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.active_tasks_count);
        }
        
        if (data.completed_this_week !== undefined) {
          const col = headers.indexOf('completed_this_week');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.completed_this_week);
        }
        
        if (data.completion_rate !== undefined) {
          const col = headers.indexOf('completion_rate');
          if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(data.completion_rate);
        }
        
        return jsonResponse({ success: true, updated: true });
      }
    }
    
    return jsonResponse({ success: true, updated: false, message: 'Wing not found' });
  } catch (error) {
    return errorResponse(error.toString());
  }
}

/**
 * Handle meeting updates (attendance count, status, etc.)
 */
function handleMeetingsUpdate(data) {
  try {
    const allIds = getAllSpreadsheetIds();
    
    for (const ssId of allIds) {
      let ss;
      try { ss = SpreadsheetApp.openById(ssId); } catch(e) { continue; }
      const sheet = ss.getSheetByName('Meetings');
      if (!sheet) continue;
      
      const rows = sheet.getDataRange().getValues();
      if (rows.length === 0) continue;
      const headers = rows[0];
      
      const msgIdCol = headers.indexOf('message_id');
      const meetingIdCol = headers.indexOf('meeting_id');
      const attendeeCountCol = headers.indexOf('attendee_count');
      const statusCol = headers.indexOf('status');
      
      if (msgIdCol === -1 && meetingIdCol === -1) continue;
      
      for (let i = 1; i < rows.length; i++) {
        const matchMsg = data.message_id && String(rows[i][msgIdCol]) === String(data.message_id);
        const matchMeeting = data.meeting_id && String(rows[i][meetingIdCol]) === String(data.meeting_id);
        
        if (matchMsg || matchMeeting) {
          if (data.status === 'Deleted') {
            sheet.deleteRow(i + 1);
            return jsonResponse({ success: true, updated: true, message: 'Row deleted' });
          }
          if (data.attendee_count !== undefined && attendeeCountCol !== -1) sheet.getRange(i + 1, attendeeCountCol + 1).setValue(data.attendee_count);
          if (data.status && statusCol !== -1) sheet.getRange(i + 1, statusCol + 1).setValue(data.status);
          return jsonResponse({ success: true, updated: true });
        }
      }
    }
    return jsonResponse({ success: true, updated: false, message: 'Meeting not found' });
  } catch (error) {
    return errorResponse(error.toString());
  }
}

// ============ SHEET DEFINITIONS ============

/**
 * Define column headers for each sheet type
 */
function getHeadersForSheet(sheetName) {
  const definitions = {
    'Tasks': [
      'task_id', 'title', 'description', 'status', 'deadline', 
      'requester', 'assignee', 'wing', 'priority', 'message_id', 
      'created_at', 'updated_at', 'target_type', 'collaboration', 'reminder_sent',
      'metric_type', 'metric_current', 'metric_total', 'metric_unit', 
      'reminder_frequency_hours', 'last_reminder_sent', 'showcase_message_id', 'parent_id', 'channel_id'
    ],
    'Meetings': [
      'meeting_id', 'wing', 'title', 'agenda', 'scheduled_time', 
      'duration', 'created_by', 'created_at', 'attendee_count', 
      'attendee_names', 'message_id', 'status'
    ],
    'WingShowcase': [
      'wing_name', 'channel_id', 'weekly_message_id', 'monthly_message_id',
      'last_updated', 'active_tasks_count', 'completed_this_week', 'completion_rate'
    ],
    'Updates': [
      'update_id', 'wing', 'type', 'submitter', 'timestamp',
      'content1', 'content2', 'content3', 'content4'
    ],
    'Members': [
      'Name', 'Role', 'Status'
    ],
    'DelayTracker': [
      'Task_id', 'Name', 'Why delay', 'Delay counter', 'Task update', 'wing'
    ],
    'ScoreBoards': [
      'Name', 'Total Tasks assigned', 'Total done', 'Pace', 'Delay days count', 
      'Overall delay scores', 'Remarks', 'wing'
    ],
    'ReminderChannels': [
      'wing_name', 'channel_id'
    ],
    'VisionPlans': [
      'plan_id', 'wing', 'type', 'vision_statement', 'targets', 'created_by', 'created_at', 'status'
    ]
  };
  
  return definitions[sheetName] || [];
}

/**
 * Specialized formatting for VisionPlans
 */
function formatVisionPlansSheet(sheet) {
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2) return;

  const range = sheet.getRange(2, 1, lastRow - 1, lastCol);
  
  // Basic formatting
  range.setVerticalAlignment('top');
  range.setWrap(true);
  
  // Alternating row colors for readability
  for (let i = 2; i <= lastRow; i++) {
    const rowRange = sheet.getRange(i, 1, 1, lastCol);
    if (i % 2 === 0) {
      rowRange.setBackground('#f8f9fa');
    } else {
      rowRange.setBackground('#ffffff');
    }
    
    // Status color coding
    const statusCol = 8; // 'status' is the 8th column
    const status = sheet.getRange(i, statusCol).getValue();
    const statusCell = sheet.getRange(i, statusCol);
    
    if (status === 'Active') {
      statusCell.setFontColor('#1e7e34').setFontWeight('bold');
    } else if (status === 'Archived') {
      statusCell.setFontColor('#6c757d').setFontWeight('normal');
    }
  }
  
  // Set column widths
  sheet.setColumnWidth(1, 120); // plan_id
  sheet.setColumnWidth(2, 100); // wing
  sheet.setColumnWidth(3, 80);  // type
  sheet.setColumnWidth(4, 300); // vision_statement
  sheet.setColumnWidth(5, 400); // targets
  sheet.setColumnWidth(6, 120); // created_by
  sheet.setColumnWidth(7, 150); // created_at
  sheet.setColumnWidth(8, 80);  // status
  
  // Add borders
  range.setBorder(true, true, true, true, true, true, '#dee2e6', SpreadsheetApp.BorderStyle.SOLID);
}

// ============ UTILITY FUNCTIONS ============

/**
 * Format header row with styling
 */
function formatHeaderRow(sheet, numColumns) {
  const headerRange = sheet.getRange(1, 1, 1, numColumns);
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#4285f4');
  headerRange.setFontColor('#ffffff');
  headerRange.setHorizontalAlignment('center');
  sheet.setFrozenRows(1);
}

/**
 * Create JSON success response
 */
function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Create JSON error response
 */
function errorResponse(msg) {
  return ContentService
    .createTextOutput(JSON.stringify({ error: msg }))
    .setMimeType(ContentService.MimeType.JSON);
}

// ============ INITIALIZATION FUNCTION ============

/**
 * Initialize all sheets with proper formatting
 * Run this once manually from the Apps Script editor
 */
function initializeSheets() {
  const allIds = getAllSpreadsheetIds();
  const adminOnlySheets = ['Members', 'DelayTracker', 'ScoreBoards', 'WingShowcase', 'Updates', 'ReminderChannels'];
  const commonSheets = ['Tasks', 'Meetings', 'VisionPlans'];
  
  allIds.forEach(ssId => {
    try {
      const ss = SpreadsheetApp.openById(ssId);
      const isDefault = (ssId === DEFAULT_SPREADSHEET_ID);
      
      // If it's the main sheet, create everything. 
      // If it's a wing sheet, create only Tasks and Meetings.
      const sheetNames = isDefault ? [...adminOnlySheets, ...commonSheets] : commonSheets;
      
      Logger.log(`Initializing Spreadsheet: ${ss.getName()} (${ssId})`);
      
      sheetNames.forEach(name => {
        let sheet = ss.getSheetByName(name);
        if (!sheet) {
          Logger.log(`  - Creating sheet: ${name}`);
          sheet = ss.insertSheet(name);
          const headers = getHeadersForSheet(name);
          if (headers.length > 0) {
            sheet.appendRow(headers);
            formatHeaderRow(sheet, headers.length);
            for (let i = 1; i <= headers.length; i++) {
              sheet.autoResizeColumn(i);
            }
          }
        } else {
          Logger.log(`  - Sheet already exists: ${name}`);
        }
      });
    } catch (e) {
      Logger.log(`Error accessing spreadsheet ${ssId}: ${e.toString()}`);
    }
  });
  
  Logger.log('✅ Global Initialization complete!');
}

// ============ ANALYTICS FUNCTIONS ============

/**
 * Calculate wing metrics (can be called from bot or manually)
 */
function calculateWingMetrics(wingName) {
  const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
  const sheet = ss.getSheetByName('Tasks');
  
  if (!sheet) return { error: 'Tasks sheet not found' };
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const wingCol = headers.indexOf('wing');
  const statusCol = headers.indexOf('status');
  
  if (wingCol === -1 || statusCol === -1) {
    return { error: 'Required columns not found' };
  }
  
  let total = 0, done = 0, inProgress = 0, todo = 0;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][wingCol] === wingName && data[i][statusCol] !== 'Deleted') {
      total++;
      const status = data[i][statusCol];
      if (status === 'Done') done++;
      else if (status === 'InProgress') inProgress++;
      else if (status === 'Todo') todo++;
    }
  }
  
  return {
    wing: wingName,
    total: total,
    done: done,
    inProgress: inProgress,
    todo: todo,
    completionRate: total > 0 ? Math.round((done / total) * 100) : 0
  };
}

/**
 * Get overdue tasks across all wings
 */
function getOverdueTasks() {
  const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
  const sheet = ss.getSheetByName('Tasks');
  
  if (!sheet) return [];
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const deadlineCol = headers.indexOf('deadline');
  const statusCol = headers.indexOf('status');
  const titleCol = headers.indexOf('title');
  const assigneeCol = headers.indexOf('assignee');
  const wingCol = headers.indexOf('wing');
  
  const overdue = [];
  const now = new Date();
  
  for (let i = 1; i < data.length; i++) {
    const status = data[i][statusCol];
    const deadlineStr = data[i][deadlineCol];
    
    if (status !== 'Done' && status !== 'Deleted' && deadlineStr) {
      try {
        const deadline = new Date(deadlineStr);
        if (deadline < now) {
          overdue.push({
            title: data[i][titleCol],
            assignee: data[i][assigneeCol],
            wing: data[i][wingCol],
            deadline: deadlineStr,
            daysOverdue: Math.floor((now - deadline) / (1000 * 60 * 60 * 24))
          });
        }
      } catch (e) {
        // Invalid date format, skip
      }
    }
  }
  
  return overdue;
}

/**
 * Export wing data to formatted report
 */
function exportWingReport(wingName) {
  const metrics = calculateWingMetrics(wingName);
  const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
  
  // Create or get Reports sheet
  let reportSheet = ss.getSheetByName('Reports');
  if (!reportSheet) {
    reportSheet = ss.insertSheet('Reports');
  }
  
  reportSheet.clear();
  
  // Add report header
  reportSheet.appendRow([`${wingName} Wing Report - Generated ${new Date().toLocaleDateString()}`]);
  reportSheet.appendRow([]);
  reportSheet.appendRow(['Metric', 'Value']);
  reportSheet.appendRow(['Total Tasks', metrics.total]);
  reportSheet.appendRow(['Completed', metrics.done]);
  reportSheet.appendRow(['In Progress', metrics.inProgress]);
  reportSheet.appendRow(['Todo', metrics.todo]);
  reportSheet.appendRow(['Completion Rate', `${metrics.completionRate}%`]);
  
  // Format report
  reportSheet.getRange(1, 1).setFontSize(14).setFontWeight('bold');
  reportSheet.getRange(3, 1, 1, 2).setFontWeight('bold').setBackground('#4285f4').setFontColor('#ffffff');
  
  Logger.log(`Report generated for ${wingName}`);
  return reportSheet.getUrl();
}

// ============ TESTING FUNCTIONS ============

/**
 * Test the API endpoints
 * Run this to verify everything is working
 */
function testAPI() {
  Logger.log('Starting API tests...');
  
  // Test 1: Check if sheets exist
  const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
  const requiredSheets = ['Tasks', 'Meetings', 'WingShowcase'];
  
  requiredSheets.forEach(name => {
    const sheet = ss.getSheetByName(name);
    if (sheet) {
      Logger.log(`✅ ${name} sheet exists`);
    } else {
      Logger.log(`❌ ${name} sheet missing`);
    }
  });
  
  // Test 2: Verify column headers
  const tasksSheet = ss.getSheetByName('Tasks');
  if (tasksSheet) {
    const headers = tasksSheet.getRange(1, 1, 1, tasksSheet.getLastColumn()).getValues()[0];
    Logger.log(`Tasks sheet has ${headers.length} columns`);
    Logger.log(`Headers: ${headers.join(', ')}`);
  }
  
  Logger.log('✅ API tests complete!');
}

/**
 * Handle processing of delays and calculating scoreboards
 */
function handleProcessDelays(data) {
  try {
    const tasksDataRaw = getAllDataFromSheet('Tasks');
    if (tasksDataRaw.length === 0) return jsonResponse({ success: true, message: 'No tasks found' });

    const tasksHeaders = tasksDataRaw[0];
    const tIdIdx = tasksHeaders.indexOf('task_id');
    const tAssignIdx = tasksHeaders.indexOf('assignee');
    const tDeadIdx = tasksHeaders.indexOf('deadline');
    const tStatusIdx = tasksHeaders.indexOf('status');
    const tPriorityIdx = tasksHeaders.indexOf('priority');
    const tWingIdx = tasksHeaders.indexOf('wing');

    const wingsToProcess = ["General", ...Object.keys(WING_SPREADSHEETS)];
    const now = new Date();

    // Group tasks by wing for efficient processing
    const tasksByWing = {};
    for (let i = 1; i < tasksDataRaw.length; i++) {
        const wing = tasksDataRaw[i][tWingIdx] || "General";
        if (!tasksByWing[wing]) tasksByWing[wing] = [];
        tasksByWing[wing].push(tasksDataRaw[i]);
    }

    // Get members from default spreadsheet
    const defaultSs = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
    const memberSheet = defaultSs.getSheetByName('Members');
    const membersData = memberSheet ? memberSheet.getDataRange().getValues() : [];
    const mNameIdx = membersData.length > 0 ? membersData[0].indexOf('Name') : -1;
    const mRoleIdx = membersData.length > 0 ? membersData[0].indexOf('Role') : -1;

    for (const wing of wingsToProcess) {
        const targetSsId = (wing === "General") ? DEFAULT_SPREADSHEET_ID : (WING_SPREADSHEETS[wing] || DEFAULT_SPREADSHEET_ID);
        if (targetSsId === "PASTE_ID_HERE") continue;

        let ss;
        try { ss = SpreadsheetApp.openById(targetSsId); } catch(e) { continue; }
        
        // Ensure sheets exist
        const delaySheetName = 'DelayTracker';
        const scoreSheetName = 'ScoreBoards';
        
        let delaySheet = ss.getSheetByName(delaySheetName);
        if(!delaySheet) {
          delaySheet = ss.insertSheet(delaySheetName);
          const headers = getHeadersForSheet(delaySheetName);
          delaySheet.appendRow(headers);
          formatHeaderRow(delaySheet, headers.length);
        }
        
        let scoreSheet = ss.getSheetByName(scoreSheetName);
        if(!scoreSheet) {
          scoreSheet = ss.insertSheet(scoreSheetName);
          const headers = getHeadersForSheet(scoreSheetName);
          scoreSheet.appendRow(headers);
          formatHeaderRow(scoreSheet, headers.length);
        }

        const wingTasks = tasksByWing[wing] || [];
        const delayHeaders = getHeadersForSheet(delaySheetName);
        const dIdIdx = delayHeaders.indexOf('Task_id');
        const dNameIdx = delayHeaders.indexOf('Name');
        const dCounterIdx = delayHeaders.indexOf('Delay counter');
        const dWingIdx = delayHeaders.indexOf('wing');

        const delayData = delaySheet.getDataRange().getValues();
        let currentDelays = {};
        for(let j=1; j<delayData.length; j++){
          if(delayData[j][dIdIdx]) {
            currentDelays[delayData[j][dIdIdx]] = { rowIdx: j, count: parseInt(delayData[j][dCounterIdx]) || 0 };
          }
        }

        // 1. Process Delays for this wing
        for (const row of wingTasks) {
            const status = row[tStatusIdx];
            const deadlineStr = row[tDeadIdx];
            
            if (status !== 'Done' && status !== 'Deleted' && deadlineStr) {
                try {
                    const deadline = new Date(deadlineStr);
                    if (deadline < now) {
                        const taskId = row[tIdIdx];
                        const assignee = row[tAssignIdx];
                        const daysOver = Math.max(1, Math.floor((now - deadline) / (1000 * 60 * 60 * 24)));

                        if(currentDelays[taskId] !== undefined) {
                             delaySheet.getRange(currentDelays[taskId].rowIdx + 1, dCounterIdx + 1).setValue(daysOver);
                        } else {
                             // Task_id, Name, Why delay, Delay counter, Task update, wing
                             delaySheet.appendRow([taskId, assignee, '', daysOver, 'no', wing]);
                        }
                    }
                } catch(e) {}
            }
        }

        // 2. Process ScoreBoard for this wing
        scoreSheet.clearContents();
        const scoreHeaders = getHeadersForSheet(scoreSheetName);
        scoreSheet.appendRow(scoreHeaders);
        formatHeaderRow(scoreSheet, scoreHeaders.length);
        
        const finalDelayData = delaySheet.getDataRange().getValues();
        
        // Find members relevant to this wing
        const wingMembers = new Set();
        for (const t of wingTasks) if (t[tAssignIdx]) wingMembers.add(t[tAssignIdx]);
        
        // Also add members from Members sheet who have this wing as their Role
        if (mNameIdx !== -1 && mRoleIdx !== -1) {
          for (let i = 1; i < membersData.length; i++) {
            if (membersData[i][mRoleIdx] === wing) {
              wingMembers.add(membersData[i][mNameIdx]);
            }
          }
        }

        for (const memberName of wingMembers) {
            let totalAssigned = 0;
            let totalDone = 0;
            let delayDaysCount = 0;
            let overallScore = 0;

            for(const t of wingTasks){
                if(t[tAssignIdx] === memberName){
                    totalAssigned++;
                    if(t[tStatusIdx] === 'Done') {
                        totalDone++;
                        const priority = t[tPriorityIdx];
                        if (priority === 'High') overallScore += 15;
                        else if (priority === 'Low') overallScore += 5;
                        else overallScore += 10;
                    }
                }
            }

            for(let j=1; j<finalDelayData.length; j++) {
                if(finalDelayData[j][dNameIdx] === memberName) {
                    delayDaysCount += parseInt(finalDelayData[j][dCounterIdx]) || 0;
                }
            }

            overallScore -= Math.floor(delayDaysCount / 2);
            if (overallScore < 0) overallScore = 0;

            let pace = "0%";
            let remarks = "New/Not Started";
            if (totalAssigned > 0) {
                pace = Math.round((totalDone / totalAssigned) * 100) + "%";
                if (overallScore >= totalAssigned * 5 && totalDone > 0) remarks = "Green";
                else if (overallScore >= totalAssigned * 2 && totalDone > 0) remarks = "Orange";
                else remarks = "Red";
            }
            
            // Name, assigned, done, Pace, Delay days, Overall points, Remarks, wing
            scoreSheet.appendRow([memberName, totalAssigned, totalDone, pace, delayDaysCount, overallScore, remarks, wing]);
        }
        
        // Protection
        try {
            const p = delaySheet.protect().setDescription('Admin Only');
            p.removeEditors(p.getEditors());
        } catch(e){}
    }

    return jsonResponse({ success: true, message: 'Delays and Scores processed for all wings' });
  } catch(e){
      return errorResponse(e.toString());
  }
}

/**
 * Handle updates to ReminderChannels sheet
 * If wing already exists, update the channel_id, otherwise append a new row
 */
function handleReminderChannelsUpdate(data) {
  try {
    const ss = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
    let sheet = ss.getSheetByName('ReminderChannels');
    
    if (!sheet) {
      sheet = ss.insertSheet('ReminderChannels');
      const headers = getHeadersForSheet('ReminderChannels');
      sheet.appendRow(headers);
      formatHeaderRow(sheet, headers.length);
    }
    
    const rows = sheet.getDataRange().getValues();
    const headers = rows[0];
    const wingCol = headers.indexOf('wing_name');
    const channelCol = headers.indexOf('channel_id');
    
    let existingRowIndex = -1;
    for (let i = 1; i < rows.length; i++) {
      if (rows[i][wingCol] === data.wing_name) {
        existingRowIndex = i;
        break;
      }
    }
    
    if (existingRowIndex !== -1) {
      sheet.getRange(existingRowIndex + 1, channelCol + 1).setValue(data.channel_id);
      return jsonResponse({ success: true, updated: true });
    } else {
      const newRow = [];
      headers.forEach(h => {
        if (h === 'wing_name') newRow.push(data.wing_name);
        else if (h === 'channel_id') newRow.push(data.channel_id);
        else newRow.push('');
      });
      sheet.appendRow(newRow);
      return jsonResponse({ success: true, updated: false, appended: true });
    }
  } catch (error) {
    return errorResponse(error.toString());
  }
}
