local delay = 1 -- delay in seconds between each deposit
local stop = false

local itemsToDeposit = {
    ['Dull Spined Clam'] = true, 
    ['Ribbed Mollusk Meat'] = true, 
    ['Scalebelly Mackerel'] = true, 
    ['Temporal Dragonhead'] = true,
    ['Thousandbite Piranha'] = true,
    ['Islefin Dorado'] = true,
    ['Cerulean Spinefish'] = true,
    ['Aileron Seamoth'] = true,
    ['Soggy Clump of Darkmoon Cards'] = true,
    ['Schematic'] = true, -- Schematic: recipes
    ['Plans'] = true, -- Plans: recipes
    ['Technique'] = true, -- Technique: recipes
    ['Recipe'] = true, -- Recipe: recipes
    ['Pattern'] = true -- Pattern: recipes
}

-- Function to check if an item should be deposited
local function checkItemValid(itemID)
    local itemName = GetItemInfo(itemID)
    print("Checking if item name should be deposited: " ..itemName)
    for item, _ in pairs(itemsToDeposit) do
        -- print("Checking against item: " ..item)
        if string.find(itemName, item) then
            return true
        end
    end
    return false
end

-- Function to deposit an item after checking that it should be
local function depositNextItem(bag, slot)
    if stop then return end
    if slot > C_Container.GetContainerNumSlots(bag) then
        -- All items in the current bag have been processed
        if bag < NUM_TOTAL_EQUIPPED_BAG_SLOTS then
            -- Process the next bag
            depositNextItem(bag + 1, 1)
        else
            -- All items have been processed
            print("Finished depositing items.")
        end
    else
        local itemID = C_Container.GetContainerItemID(bag, slot)
        if not itemID then
            -- Skip empty slot
            depositNextItem(bag, slot + 1)
        elseif checkItemValid(itemID) then
            -- Deposit the item
            C_Timer.After(delay, function()
                C_Container.UseContainerItem(bag, slot)
                depositNextItem(bag, slot + 1)
            end)
        else
            -- Skip item
            depositNextItem(bag, slot + 1)
        end
    end
end

-- Function to find a bank tab with available space to deposit our items.
function findAvailableBankTab()
    print("Finding bank tab with available space")
    for tab = 1, GetNumGuildBankTabs() do
        SetCurrentGuildBankTab(tab)
        -- QueryGuildBankTab(tab)
        print("Checking bank tab: "..tab)
        local lastSlot = GetGuildBankItemInfo(tab, 98)
        if lastSlot == nil then
            print("Found guild bank tab with available space: " ..tab)
            return true
        end
    end
    return false
end

-- Create a frame to listen for the PLAYER_INTERACTION_MANAGER_FRAME_SHOW event
local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_INTERACTION_MANAGER_FRAME_SHOW");
frame:RegisterEvent("PLAYER_INTERACTION_MANAGER_FRAME_HIDE");

-- Define the event handler function
function frame:OnEvent(event, arg1)
    if event == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" then
        if arg1 == 10 then -- Guild Bank
            print("GBank opened")
            stop = false
            if findAvailableBankTab() then
                print("Depositing items")
                depositNextItem(BACKPACK_CONTAINER, 1)
            end
        end
    elseif event == "PLAYER_INTERACTION_MANAGER_FRAME_HIDE" then
        if arg1 == 10 then
            print("Stopping")
            stop = true
        end
    end
end

-- Set the frame's event handler
frame:SetScript("OnEvent", frame.OnEvent)
