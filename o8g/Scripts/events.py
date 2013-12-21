    # Python Scripts for the Android:Netrunner LCG definition for OCTGN
    # Copyright (C) 2012  Konstantine Thoukydides

    # This python script is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this script.  If not, see <http://www.gnu.org/licenses/>.

###==================================================File Contents==================================================###
# This file contains the basic table actions in ANR. They are the ones the player calls when they use an action in the menu.
# Many of them are also called from the autoscripts.
###=================================================================================================================###

import re
import collections
import time

def chkTwoSided():
   mute()
   if not table.isTwoSided(): information(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and make sure  the appropriate button is checked")
   versionCheck()
   fetchCardScripts() # We only download the scripts at the very first setup of each play session.
   chooseSide()
   hardcoreMode = getSetting('HARDCORE', False) #We check what the stored value for HARDCORE more is, so that we can restore it if true
   if hardcoreMode: 
      Automations['HARDCORE'] = True
      notify ("--> {} trusts their feelings. HARDCORE mode activated!".format(me))
      me.setGlobalVariable('Switches',str(Automations))

def loadDeck(player,groups):   
   if player == me:
      if setupSide(): checkDeckLegality()
   
def setupSide():
   global Side, Affiliation
   for card in me.hand:
      if card.Type != 'Affiliation': 
         whisper(":::Warning::: You are not supposed to have any non-Affiliation cards in your hand when you start the game")
         if card.Type == 'Objective': card.moveToBottom(objectives)
         else: card.moveToBottom(deck)
         continue
      else: 
         Side = card.Side
         storeSpecial(card)
         me.setGlobalVariable('Side', Side)
         Affiliation = card
   if not Side: 
      confirm("You need to have your Affiliation card in your hand when you try to setup the game. If you have it in your deck, please look for it and put it in your hand before running this function again")
      return False
   return True
   
def checkDeckLegality():
   if debugVerbosity >= 1: notify(">>> checkDeckLegality()") #Debug
   mute()
   notify ("--> Checking deck of {} ...".format(me))
   ok = True
   commandDeck = me.piles['Command Deck']
   objectiveDeck = me.piles['Objective Deck']
   if debugVerbosity >= 4: notify("### About to compare deck sizes.") #Debug
   if len(objectiveDeck) != len(commandDeck) / 5: 
      ok = False
      notify(":::ERROR::: {}'s decks do not sync (Nr. of objective cards ({}) =/= Nr. of command cards ({}) / 5.".format(me,len(objectiveDeck),len(commandDeck)))
   if debugVerbosity >= 4: notify("### About to move cards into scripting pile") #Debug
   for card in objectiveDeck: card.moveTo(me.ScriptingPile)
   for card in commandDeck: card.moveTo(me.ScriptingPile)
   rnd(1,10)
   if debugVerbosity >= 4: notify("### About to check each card in the decks") #Debug
   objectiveBlocks = []
   commandBlocks = []
   limitedBlocksFound = []
   podList = []
   for card in me.ScriptingPile: 
      #if ok == False: continue # If we've already found illegal cards, no sense in checking anymore. Will activate this after checking
      if card.Type == 'Objective': 
         objectiveBlocks.append((card.name,card.Block)) # We store a tuple of objective name and objective block
         podList.append(num(card.Block)) # We also store the objective's block in an extra list which we later use for stats
      else:
         commandBlocks.append((card.name,card.Block,card.properties['Block Number'])) # We store a tuple of the card name, objective block and number in that block
      if card.Side != Side: 
         notify(":::ERROR::: Opposing card found in {}'s deck: {}".format(me,card))
         ok = False
      if re.search(r'Limit 1 per objective deck',card.Text):
         if card.Block in limitedBlocksFound: 
            notify(":::ERROR::: Duplicate Limited Objective found in {}'s deck: {}".format(me,card))
            ok = False
         else: limitedBlocksFound.append(card.Block)
      limitedAffiliation = re.search(r'([A-Za-z ]+) affiliation only\.',card.Text)
      if limitedAffiliation:
         if debugVerbosity >= 2: notify("#### Limited Affiliation ({}) card found: {}".format(limitedAffiliation.group(1),card))
         if limitedAffiliation.group(1) != Affiliation.Affiliation:
            notify(":::ERROR::: Restricted Affiliation Objective found in {}'s deck: {}".format(me,card))
            ok = False
   for objective in objectiveBlocks:
      if debugVerbosity >= 4: notify("#### Checking Objective Block {} ({})".format(objective[1],objective[0]))
      blocks = []
      commandBlocksSnapshot = list(commandBlocks)
      for command in commandBlocksSnapshot:
         if command[1] == objective[1] and command[2] not in blocks:
            if debugVerbosity >= 4: notify("#### Block {} Command {} found".format(command[1],command[2]))
            blocks.append(command[2])
            commandBlocks.remove(command)
      if len(blocks) < 5: 
         notify(":::ERROR::: Objective Block {} ({}) not complete. (only {} out of 5 found: {})".format(objective[1],objective[0],len(blocks),blocks))
         ok = False
   if len(commandBlocks): # If there's still cards in this list, it means it wasn't matched with an objective block, so it's an orphan
      notify(":::ERROR::: Orphan command cards found in {}'s deck: {}".format(me,[command[0] for command in commandBlocks]))
      ok = False
   rnd(1,10)      
   for card in me.ScriptingPile: 
      if card.Type == 'Objective': card.moveTo(objectiveDeck)
      else: card.moveTo(commandDeck)
   if ok: notify(" -> Deck of {} is OK!".format(me))
   else: 
      notify(" -> Deck of {} is Illegal!".format(me))
      information("We have found illegal cards in your deck. Please load a legal deck!")
   if debugVerbosity >= 3: notify("<<< checkDeckLegality() with return: {}".format(ok)) #Debug
   debugNotify("pods = {}".format(str(podList).replace(" ", "")))
   me.setGlobalVariable('Pods',str(podList).replace(" ", ""))
   
def parseNewCounters(player,counter,oldValue):
   mute()
   debugNotify(">>> parseNewCounters() for player {} with counter {}. Old Value = {}".format(player,counter.name,oldValue))
   if counter.name == 'Death Star Dial':
      for player in getPlayers(): 
         if player.counters['Death Star Dial'].value != counter.value: player.counters['Death Star Dial'].value = counter.value
   debugNotify("<<< parseNewCounters()")

def checkMovedCard(player,card,fromGroup,toGroup,oldIndex,index,oldX,oldY,x,y,isScriptMove):
   mute()
   if isScriptMove: return # If the card move happened via a script, then all automations should have happened already.
   if fromGroup == me.hand and toGroup == table: 
      return # Not implemented yet
   if toGroup == me.piles['Common Reserve']:
      if card.Type == "Objective":
         whisper(":::ERROR::: You cannot put objectives in your common reserve")
         card.moveTo(fromGroup)
         return # We forcefully quit so that we don't clear attachments yet
      if len(toGroup) > 1: # If they moved a card into the common reserve while another was already in, then we clear the common reserve as well.
         for c in toGroup:
            if c != card: 
               c.moveTo(me.piles['Discard Pile'])
               notify(":> {} discarded 1 card from their Common Reserve".format(me))
   elif fromGroup == table and toGroup == table and card.controller == me: # If the player dragged a card manually to a different location on the table, we want to re-arrange the attachments
      if card.Type == 'Objective' or card.Type == 'Unit': 
         update()
         orgAttachments(card) 
   if fromGroup == table and toGroup != table and card.owner == me: # If the player dragged a card manually from the table to their discard pile...
      debugNotify("Clearing card attachments")
      clearAttachLinks(card)      
      