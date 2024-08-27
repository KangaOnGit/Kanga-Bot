# Discord-Bot

# Running on VS Code/Local

1. Create a folder named "Discord Bot"

   + Open cmd, in cmd type ```cd [Path to folder]```
   + After changing the directory to the folder, do ```git clone https://github.com/KangaOnGit/Kanga-Bot.git```

2. Create an Application on [Discord Developer Portal](https://discord.com/developers/applications)
  
3. In Settings, go to [Bot](https://github.com/user-attachments/assets/b9f26c28-6cd1-4254-ad2d-e038cbd18e39)
   
   + Click on [Reset Token](https://github.com/user-attachments/assets/c642ce8d-cae1-4be2-8fce-a6010be2f788)
   
4. In your [Environmental Variables](https://github.com/user-attachments/assets/ca0b56d7-17ca-4897-bb61-e7a895a744a2), create a either a User Variables or System Variables (Local or Global Tokens) and name your variable "DISCORD_BOT_TOKEN"
   
   + In the "Value" field, paste in your Bot token you got from step 2
     
     > Make sure your Discord Bot's Token Environment Variable's name matches your variable name in the code

5. Download [FFmpeg](https://www.gyan.dev/ffmpeg/builds/)
   
   + Move the FFmpeg file to the same disk containing the [code](https://github.com/user-attachments/assets/39313cbd-18ac-4192-bc62-df934fa72c32)
  
6. Open the Discord Bot folder in your IDE
7. Run app.py

# Running on Google Collab

1. Clone the code into your Google Collab's new Notebook
2. Replace the DISCORD_BOT_TOKEN with your actual Discord Bot Token that you got
3. Run all of the Cells
