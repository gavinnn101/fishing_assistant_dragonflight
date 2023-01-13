local delay = 1 -- delay in seconds

-- Define the function that deposits items
local function depositItem(bag, slot)
    local itemID = C_Container.GetContainerItemID(bag, slot)
    if itemID then
        -- Skip item if it's soulbound
        if C_Item.IsBound(ItemLocation:CreateFromBagAndSlot(bag, slot)) then
            print("Skipping soulbound item: " ..itemID)
        else
            print("Interacting with item: " ..itemID)
            -- Pickup item
            C_Container.UseContainerItem(bag, slot)
            print("finished interacting with item: " ..itemID)
        end
        -- Find the next item to deposit
        for i = slot + 1, C_Container.GetContainerNumSlots(bag) do
            if C_Container.GetContainerItemID(bag, i) then
                -- Deposit the next item after the delay
                C_Timer.After(delay, function() depositItem(bag, i) end)
                return
            end
        end
        for i = 0, NUM_BAG_SLOTS do
            if i ~= bag then
                for j = 1, C_Container.GetContainerNumSlots(i) do
                    if C_Container.GetContainerItemID(i, j) then
                        -- Deposit the next item after the delay
                        C_Timer.After(delay, function() depositItem(i, j) end)
                        return
                    end
                end
            end
        end
    end
end

local function findAvailableBankTab()
    print("Finding bank tab with available space")
    local numTabs = GetNumGuildBankTabs()
    while numTabs > 0 do
        -- If the last slot (98) is available then we can deposit our item.
        local bankTab = GetCurrentGuildBankTab()
        local lastSlot = GetGuildBankItemInfo(bankTab, 98)
        if lastSlot == nil then
            print("Found guild bank slot with available space: " ..numTabs)
            return true
        end
        SetCurrentGuildBankTab(numTabs)
        numTabs = numTabs - 1
    end
    return false
end

-- Create a frame to listen for the PLAYER_INTERACTION_MANAGER_FRAME_SHOW event
local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_INTERACTION_MANAGER_FRAME_SHOW");

-- Define the event handler function
function frame:OnEvent(event, arg1)
    if event == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" then
        if arg1 == 10 then --Guild Bank
            print("GBank opened")
            -- Find bank tab with available space
            if findAvailableBankTab() then
                -- Loop over each bag on character
                for bag = BACKPACK_CONTAINER, NUM_TOTAL_EQUIPPED_BAG_SLOTS do
                    -- Loop over each slot in bag to find an item
                    for slot = 1, C_Container.GetContainerNumSlots(bag) do
                        local itemID = C_Container.GetContainerItemID(bag, slot)
                        if itemID then
                            print("Depositing item: " ..itemID.. "in bag: " ..bag)
                            depositItem(bag, slot)
                            return
                        end
                    end
                end
            else
                print("You don't have any available space in your guild bank!!!")
            end
        end
    end
end

-- Set the frame's event handler
frame:SetScript("OnEvent", frame.OnEvent)