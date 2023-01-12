-- Create a frame to listen for the PLAYER_INTERACTION_MANAGER_FRAME_SHOW event
local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_INTERACTION_MANAGER_FRAME_SHOW");

-- Define the event handler function
function frame:OnEvent(event, arg1)
    if event == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" then
        if arg1 == 10 then --Guild Bank
            print("GBank opened")
            -- Iterate over all bags
            for bag = 0, NUM_BAG_SLOTS do
                -- Iterate over all slots in the current bag
                for slot = 1, C_Container.GetContainerNumSlots(bag) do
                    -- Get item ID
                    local itemID = C_Container.GetContainerItemID(bag, slot)
                    print("itemID: " ..itemID)
                    -- Skip item if it's soulbound
                    if C_Item.IsBound(ItemLocation:CreateFromBagAndSlot(bag, slot)) then
                        print("Skipping soulbound item.")
                    else
                        print("Picking up non-soulbound item")
                        -- Pickup item after 2 seconds
                        success = C_Timer.After(2, C_Container.PickupContainerItem(bag, slot))
                        print("success: " ..success)
                        if not success then
                            print("Error picking up item: "..itemID.." from bag "..bag..", slot "..slot)
                        else
                            print("Depositing item: "..itemID.." to guild bank")
                            local tab = GetCurrentGuildBankTab()
                            local success = DepositGuildBankItem(tab, slot)
                            if not success then
                                print("Error depositing item: "..itemID.." to guild bank")
                            end
                        end
                    end
                end
            end
        end
    end
end

-- Set the frame's event handler
frame:SetScript("OnEvent", frame.OnEvent)
