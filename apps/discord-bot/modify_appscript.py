import re

with open('appscript.gs', 'r') as f:
    content = f.read()

# 1. Replace Configuration Block & Add Helpers
new_config = """// ============ CONFIGURATION ============
const DEFAULT_SPREADSHEET_ID = "1GCeoldTAcNVpNLPIpFgXd6fSS0OQQPaDEJ7sybCcK94"; 

// Configure the spreadsheet ID for each wing below. You can leave them as "PASTE_ID_HERE"
// if you want them to fallback to the default spreadsheet until you create them.
const WING_SPREADSHEETS = {
  "Product": "PASTE_ID_HERE",
  "Design": "PASTE_ID_HERE",
  "Engineering": "PASTE_ID_HERE",
  "Marketing": "PASTE_ID_HERE",
  "Sales": "PASTE_ID_HERE",
  "Operations": "PASTE_ID_HERE"
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
  } else if (data && data.wing) {
     wingName = data.wing;
  }
  
  if (wingName && WING_SPREADSHEETS[wingName] && WING_SPREADSHEETS[wingName] !== "PASTE_ID_HERE") {
     return WING_SPREADSHEETS[wingName];
  }
  return DEFAULT_SPREADSHEET_ID;
}

function getAllDataFromSheet(sheetName) {
  const allIds = getAllSpreadsheetIds();
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
    }
  }
  return combinedData;
}
"""
content = re.sub(
    r'// ============ CONFIGURATION ============.*?const SPREADSHEET_ID = ".*?";', 
    new_config, 
    content, 
    flags=re.DOTALL
)

# 2. Update doGet
new_doget = """function doGet(e) {
  try {
    const sheet = e.parameter.sheet;
    if (!sheet) return errorResponse('Sheet parameter required');
    
    const combinedData = getAllDataFromSheet(sheet);
    if (combinedData.length === 0) return errorResponse(`Sheet "${sheet}" not found or empty`);
    
    return jsonResponse(combinedData);
  } catch (error) {
    return errorResponse(error.toString());
  }
}"""
content = re.sub(r'function doGet\(e\)\s*\{.*?\n\}', new_doget, content, flags=re.DOTALL)

# 3. Update doPost for standard appends
new_append = """    // Standard append operation
    const targetSsId = getTargetSpreadsheetId(sheetName, data);
    const ss = SpreadsheetApp.openById(targetSsId);"""
content = re.sub(
    r'    // Standard append operation\s+const ss = SpreadsheetApp\.openById\(SPREADSHEET_ID\);',
    new_append,
    content
)

# 4. Update handleTasksUpdate to loop correctly
new_tasks_update = """function handleTasksUpdate(data) {
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
        last_reminder: headers.indexOf('last_reminder'),
        showcase_message_id: headers.indexOf('showcase_message_id'),
        assignee: headers.indexOf('assignee'),
        parent_id: headers.indexOf('parent_id')
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
          if (data.last_reminder !== undefined && colIndices.last_reminder !== -1) sheet.getRange(i + 1, colIndices.last_reminder + 1).setValue(data.last_reminder);
          if (data.showcase_message_id !== undefined && colIndices.showcase_message_id !== -1) sheet.getRange(i + 1, colIndices.showcase_message_id + 1).setValue(data.showcase_message_id);
          if (data.parent_id !== undefined && colIndices.parent_id !== -1) sheet.getRange(i + 1, colIndices.parent_id + 1).setValue(data.parent_id);
          if (colIndices.updated_at !== -1) sheet.getRange(i + 1, colIndices.updated_at + 1).setValue(new Date().toISOString());
          return jsonResponse({ success: true, updated: true, row: i + 1 });
        }
      }
    }
    return jsonResponse({ success: true, updated: false, message: 'No matching task found' });
  } catch (error) {
    return errorResponse(error.toString());
  }
}"""
content = re.sub(r'function handleTasksUpdate\(data\)\s*\{.*?\n\}', new_tasks_update, content, flags=re.DOTALL)

# 5. Update handleMeetingsUpdate
new_meetings_update = """function handleMeetingsUpdate(data) {
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
        const matchMeeting = data.message_id && String(rows[i][meetingIdCol]) === String(data.meeting_id);
        
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
}"""
content = re.sub(r'function handleMeetingsUpdate\(data\)\s*\{.*?\n\}', new_meetings_update, content, flags=re.DOTALL)

# 6. Update handleProcessDelays (It only writes to DEFAULT_SPREADSHEET_ID but reads mostly from it too. We should just read Tasks globally)
new_process_delays = """function handleProcessDelays(data) {
  try {
    const adminSs = SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID);
    const delaySheet = adminSs.getSheetByName('DelayTracker');
    const scoreSheet = adminSs.getSheetByName('ScoreBoards');
    const memberSheet = adminSs.getSheetByName('Members');
    
    if (!delaySheet || !scoreSheet || !memberSheet) return errorResponse('Missing admin sheets');

    const tasksData = getAllDataFromSheet('Tasks');
    const delayData = delaySheet.getDataRange().getValues();
    const membersData = memberSheet.getDataRange().getValues();

    if (tasksData.length === 0) return jsonResponse({ success: true, message: 'No tasks found' });

    const tasksHeaders = tasksData[0];
    const tIdIdx = tasksHeaders.indexOf('task_id');
    const tAssignIdx = tasksHeaders.indexOf('assignee');
    const tDeadIdx = tasksHeaders.indexOf('deadline');
    const tStatusIdx = tasksHeaders.indexOf('status');

    const delayHeaders = delayData.length > 0 ? delayData[0] : getHeadersForSheet('DelayTracker');
    const dIdIdx = delayHeaders.indexOf('Task_id');
    const dNameIdx = delayHeaders.indexOf('Name');
    const dCounterIdx = delayHeaders.indexOf('Delay counter');

    const now = new Date();

    let currentDelays = {};
    for(let j=1; j<delayData.length; j++){
      if(delayData[j][dIdIdx]){
         currentDelays[delayData[j][dIdIdx]] = { rowIdx: j, count: parseInt(delayData[j][dCounterIdx]) || 0 };
      }
    }

    for (let i = 1; i < tasksData.length; i++) {
        const row = tasksData[i];
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
                         delaySheet.appendRow([taskId, assignee, '', daysOver, 'no']);
                    }
                }
            } catch(e) {}
        }
    }

    scoreSheet.clearContents();
    const scoreHeaders = getHeadersForSheet('ScoreBoards');
    scoreSheet.appendRow(scoreHeaders);
    
    const newDelayData = delaySheet.getDataRange().getValues();
    
    for (let i = 1; i < membersData.length; i++) {
        const memberName = membersData[i][membersData[0].indexOf('Name')];
        if(!memberName) continue;

        let totalAssigned = 0;
        let totalDone = 0;
        let delayDaysCount = 0;

        for(let j=1; j<tasksData.length; j++){
            if(tasksData[j][tAssignIdx] === memberName){
                totalAssigned++;
                if(tasksData[j][tStatusIdx] === 'Done') totalDone++;
            }
        }

        for(let j=1; j<newDelayData.length; j++) {
            if(newDelayData[j][delayHeaders.indexOf('Name')] === memberName) {
               delayDaysCount += parseInt(newDelayData[j][delayHeaders.indexOf('Delay counter')]) || 0;
            }
        }

        let pace = "0%";
        let overallScore = 0;
        let remarks = "New/Not Started";
        
        if (totalAssigned > 0) {
            if (totalDone === 0) {
                overallScore = 0;
            } else {
                overallScore = 10 - Math.floor(delayDaysCount / 2);
                if (overallScore < 0) overallScore = 0;
            }
            if(overallScore > 7) remarks = "Green";
            else if(overallScore >= 5) remarks = "Orange";
            else remarks = "Red";
            pace = Math.round((totalDone / totalAssigned) * 100) + "%";
        }
        scoreSheet.appendRow([memberName, totalAssigned, totalDone, pace, delayDaysCount, overallScore, remarks]);
    }

    try {
        const p1 = delaySheet.protect().setDescription('Admin Only');
        p1.removeEditors(p1.getEditors());
    } catch(e){}

    return jsonResponse({ success: true, message: 'Delays and Scores processed' });
  } catch(e){
      return errorResponse(e.toString());
  }
}"""
content = re.sub(r'function handleProcessDelays\(data\)\s*\{.*?\n\}', new_process_delays, content, flags=re.DOTALL)

# Also fix the general references to single ss
content = content.replace("SpreadsheetApp.openById(SPREADSHEET_ID)", "SpreadsheetApp.openById(DEFAULT_SPREADSHEET_ID)")


with open('appscript_v2.gs', 'w') as f:
    f.write(content)

