//+------------------------------------------------------------------+
//|                                            OpenMT4TradingBot.mq4 |
//|                                      Copyright 2025, Immaginet Srl |
//|                           https://github.com/ImmaginetSrl/OpenMT4TradingBot |
//+------------------------------------------------------------------+
//|                                                                  |
//| MIT License                                                      |
//|                                                                  |
//| Copyright (c) 2025 Immaginet Srl                                 |
//|                                                                  |
//| Permission is hereby granted, free of charge, to any person      |
//| obtaining a copy of this software and associated documentation   |
//| files (the "Software"), to deal in the Software without          |
//| restriction, including without limitation the rights to use,     |
//| copy, modify, merge, publish, distribute, sublicense, and/or     |
//| sell copies of the Software, and to permit persons to whom the   |
//| Software is furnished to do so, subject to the following         |
//| conditions:                                                      |
//|                                                                  |
//| The above copyright notice and this permission notice shall be   |
//| included in all copies or substantial portions of the Software.  |
//|                                                                  |
//| THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,  |
//| EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES  |
//| OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND         |
//| NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT      |
//| HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,     |
//| WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     |
//| FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR    |
//| OTHER DEALINGS IN THE SOFTWARE.                                  |
//+------------------------------------------------------------------+
#property strict
#property copyright "Copyright 2025, Immaginet Srl"
#property link      "https://github.com/ImmaginetSrl/OpenMT4TradingBot"
#property version   "1.00"
#property description "Hybrid MT4-Python Trading Bot for Commodities"

// External parameters
extern string  BridgeMode = "FILE";       // Bridge mode for communication with Python
extern double  RiskPercent = 1.0;         // Risk percent of equity per trade
extern double  Lots = 0.0;                // Fixed lot size (0 = auto calculation)
extern int     MagicNumber = 20250601;    // Magic number for trade identification
extern bool    UseTrailingStop = true;    // Enable trailing stop
extern int     SignalCheckSeconds = 10;   // Seconds between signal checks
extern bool    ExportOHLC = true;         // Export OHLC data to CSV
extern string  FilePath = "OpenMT4TradingBot"; // Path for file operations

// Global variables
int lastSignalCheck = 0;
int lastBarCount = 0;
string signalFile = "signal.json";
string positionFile = "positions.json";
datetime lastSignalTimestamp = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   // Create directory if it doesn't exist
   string dataPath = StringConcatenate(TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL4\\Files\\", FilePath);
   if(!FileIsExist(dataPath, 0))
   {
      int handle = FileOpen(dataPath, FILE_WRITE|FILE_BIN);
      if(handle != INVALID_HANDLE) FileClose(handle);
   }
   
   Print("OpenMT4TradingBot initialized. Waiting for signals...");
   
   // Export initial bar data
   if(ExportOHLC) ExportBar();
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("OpenMT4TradingBot deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check for new bars
   if(lastBarCount != Bars)
   {
      lastBarCount = Bars;
      
      // Export bar data on new bar
      if(ExportOHLC) ExportBar();
   }
   
   // Check for and apply trailing stop
   if(UseTrailingStop) TrailStop();
   
   // Check for signals periodically
   if(TimeCurrent() - lastSignalCheck >= SignalCheckSeconds)
   {
      ReadSignal();
      ExportPositions();
      lastSignalCheck = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Export current bar data to CSV file                              |
//+------------------------------------------------------------------+
void ExportBar()
{
   string fileName = StringConcatenate("OHLC_", Symbol(), ".csv");
   string filePath = StringConcatenate(FilePath, "\\", fileName);
   
   // Prepare data for the last 100 bars
   int barsToExport = 100;
   if(Bars < barsToExport) barsToExport = Bars;
   
   string csvContent = "DateTime,Open,High,Low,Close,Volume\n";
   
   for(int i = barsToExport - 1; i >= 0; i--)
   {
      string line = StringFormat("%s,%f,%f,%f,%f,%d",
                                 TimeToString(Time[i], TIME_DATE|TIME_MINUTES),
                                 Open[i],
                                 High[i],
                                 Low[i],
                                 Close[i],
                                 (int)Volume[i]);
      csvContent = StringConcatenate(csvContent, line, "\n");
   }
   
   // Save to file
   int handle = FileOpen(filePath, FILE_WRITE|FILE_TXT);
   if(handle != INVALID_HANDLE)
   {
      FileWrite(handle, csvContent);
      FileClose(handle);
      Print("OHLC data exported for ", Symbol());
   }
   else
   {
      Print("Failed to export OHLC data. Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Read signal from JSON file                                       |
//+------------------------------------------------------------------+
void ReadSignal()
{
   string filePath = StringConcatenate(FilePath, "\\", signalFile);
   if(!FileIsExist(filePath)) return;
   
   int handle = FileOpen(filePath, FILE_READ|FILE_TXT);
   if(handle == INVALID_HANDLE)
   {
      Print("Error opening signal file: ", GetLastError());
      return;
   }
   
   string content = "";
   while(!FileIsEnding(handle))
   {
      content += FileReadString(handle);
   }
   FileClose(handle);
   
   // Simple JSON parsing
   if(StringLen(content) < 10) return; // Too short to be valid
   
   string symbol = ExtractJsonValue(content, "symbol");
   string direction = ExtractJsonValue(content, "direction");
   double entry = StringToDouble(ExtractJsonValue(content, "entry"));
   double sl = StringToDouble(ExtractJsonValue(content, "sl"));
   double tp = StringToDouble(ExtractJsonValue(content, "tp"));
   double lot = StringToDouble(ExtractJsonValue(content, "lot"));
   int timestamp = (int)StringToInteger(ExtractJsonValue(content, "timestamp"));
   
   // Check if this is a new signal
   if(timestamp <= lastSignalTimestamp) return;
   lastSignalTimestamp = timestamp;
   
   // Process signal
   if(symbol == Symbol())
   {
      Print("New signal for ", symbol, ": ", direction, " at ", entry);
      
      // Close existing positions for this symbol first
      ClosePositionsForSymbol();
      
      // Open new trade
      if(direction == "BUY")
      {
         OpenTrade(OP_BUY, entry, sl, tp, lot);
      }
      else if(direction == "SELL")
      {
         OpenTrade(OP_SELL, entry, sl, tp, lot);
      }
   }
}

//+------------------------------------------------------------------+
//| Extract value from JSON by key                                   |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
   string pattern = "\"" + key + "\"\\s*:\\s*";
   int start = StringFind(json, pattern);
   if(start == -1) return "";
   
   start += StringLen(pattern);
   
   // Check if the value is a string
   if(StringGetCharacter(json, start) == '\"')
   {
      start++; // Skip the opening quote
      int end = StringFind(json, "\"", start);
      return StringSubstr(json, start, end - start);
   }
   // Value is a number or boolean
   else
   {
      int end = StringFind(json, ",", start);
      if(end == -1) end = StringFind(json, "}", start);
      return StringSubstr(json, start, end - start);
   }
}

//+------------------------------------------------------------------+
//| Open new trade based on signal                                   |
//+------------------------------------------------------------------+
void OpenTrade(int type, double entry, double sl, double tp, double lot)
{
   // Calculate lot size if auto-calculation is enabled
   if(Lots <= 0 && RiskPercent > 0)
   {
      double slDist = MathAbs(entry - sl);
      double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
      double accountEquity = AccountEquity();
      double riskAmount = accountEquity * (RiskPercent / 100.0);
      
      lot = NormalizeDouble(riskAmount / (slDist * tickValue), 2);
      lot = MathMax(MarketInfo(Symbol(), MODE_MINLOT), lot);
      lot = MathMin(MarketInfo(Symbol(), MODE_MAXLOT), lot);
   }
   
   // Market order at the entry price
   int ticket = OrderSend(Symbol(), type, lot, entry, 3, sl, tp, 
                          "OpenMT4TradingBot", MagicNumber, 0, 
                          type == OP_BUY ? clrGreen : clrRed);
   
   if(ticket > 0)
   {
      Print("Trade opened: ", Symbol(), " ", (type == OP_BUY ? "BUY" : "SELL"), 
            " Lot: ", lot, " SL: ", sl, " TP: ", tp);
   }
   else
   {
      Print("Error opening trade: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Close all positions for the current symbol                      |
//+------------------------------------------------------------------+
void ClosePositionsForSymbol()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
         {
            bool result = false;
            if(OrderType() == OP_BUY)
               result = OrderClose(OrderTicket(), OrderLots(), Bid, 3, clrRed);
            else if(OrderType() == OP_SELL)
               result = OrderClose(OrderTicket(), OrderLots(), Ask, 3, clrGreen);
               
            if(!result)
               Print("Error closing order: ", GetLastError());
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Apply trailing stop to all open positions                        |
//+------------------------------------------------------------------+
void TrailStop()
{
   double atr = iATR(Symbol(), PERIOD_D1, 20, 1);
   
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
         {
            double newStopLoss = 0;
            bool modify = false;
            
            if(OrderType() == OP_BUY)
            {
               if(Bid - OrderOpenPrice() >= atr)
               {
                  newStopLoss = Bid - atr;
                  if(newStopLoss > OrderStopLoss())
                     modify = true;
               }
            }
            else if(OrderType() == OP_SELL)
            {
               if(OrderOpenPrice() - Ask >= atr)
               {
                  newStopLoss = Ask + atr;
                  if(newStopLoss < OrderStopLoss() || OrderStopLoss() == 0)
                     modify = true;
               }
            }
            
            if(modify)
            {
               bool result = OrderModify(OrderTicket(), OrderOpenPrice(), newStopLoss, OrderTakeProfit(), 0, clrBlue);
               if(!result)
                  Print("Error modifying trailing stop: ", GetLastError());
               else
                  Print("Trailing stop updated for ", Symbol(), " to ", newStopLoss);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Count positions for current EA                                   |
//+------------------------------------------------------------------+
int PositionsTotalEA()
{
   int count = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() == MagicNumber)
            count++;
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Export current positions to JSON file                            |
//+------------------------------------------------------------------+
void ExportPositions()
{
   string filePath = StringConcatenate(FilePath, "\\", positionFile);
   string content = "{\n  \"positions\": [\n";
   bool firstPosition = true;
   
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() == MagicNumber)
         {
            if(!firstPosition) content += ",\n";
            
            string type = (OrderType() == OP_BUY) ? "BUY" : "SELL";
            
            content += StringFormat("    {\n      \"ticket\": %d,\n      \"symbol\": \"%s\",\n      \"type\": \"%s\",\n      \"lots\": %.2f,\n      \"openPrice\": %.5f,\n      \"sl\": %.5f,\n      \"tp\": %.5f,\n      \"profit\": %.2f,\n      \"openTime\": %d\n    }",
                             OrderTicket(),
                             OrderSymbol(),
                             type,
                             OrderLots(),
                             OrderOpenPrice(),
                             OrderStopLoss(),
                             OrderTakeProfit(),
                             OrderProfit(),
                             OrderOpenTime());
                             
            firstPosition = false;
         }
      }
   }
   
   content += "\n  ],\n";
   content += StringFormat("  \"account\": {\n    \"balance\": %.2f,\n    \"equity\": %.2f,\n    \"margin\": %.2f,\n    \"freeMargin\": %.2f,\n    \"timestamp\": %d\n  }\n}",
                    AccountBalance(),
                    AccountEquity(),
                    AccountMargin(),
                    AccountFreeMargin(),
                    TimeCurrent());
   
   // Save to file
   int handle = FileOpen(filePath, FILE_WRITE|FILE_TXT);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, content);
      FileClose(handle);
   }
   else
   {
      Print("Failed to export positions data. Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
